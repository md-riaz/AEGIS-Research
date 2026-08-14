"""
Unit tests for aegis.server.ai_config.ProviderProfile throttling.

These pin the two properties that make concurrency real:

* the rolling-minute budget permits bursting up to ``rpm``, instead of forcing
  a ``60/rpm`` gap between every call;
* waiting for budget happens outside the lock, so one blocked caller does not
  serialise every other caller behind it.

The previous implementation violated both, which made any concurrency setting
inert: N concurrent requests still took N x (60/rpm) seconds. A test that only
asserted "the limiter eventually returns" would have passed against it, so
these assert on elapsed time.
"""

import asyncio
import time
import unittest

from aegis.server.ai_config import ProviderProfile


def profile(rpm: int, concurrency: int = 8) -> ProviderProfile:
    return ProviderProfile(
        url="http://localhost/v1/chat/completions",
        api_key="test",
        api_type="openai",
        rpm=rpm,
        concurrency=concurrency,
    )


class TestBurstingWithinBudget(unittest.TestCase):
    def test_calls_within_budget_do_not_wait(self):
        """Ten calls against a 60/min budget should be effectively instant."""
        async def scenario():
            p = profile(rpm=60)
            started = time.monotonic()
            await asyncio.gather(*(p.wait_if_needed() for _ in range(10)))
            return time.monotonic() - started

        elapsed = asyncio.run(scenario())
        # Under the old min-gap rule this was 10 x 1s = ~10s.
        self.assertLess(elapsed, 0.5, f"budgeted calls were throttled ({elapsed:.2f}s)")

    def test_no_artificial_gap_between_consecutive_calls(self):
        async def scenario():
            p = profile(rpm=30)
            started = time.monotonic()
            await p.wait_if_needed()
            await p.wait_if_needed()
            return time.monotonic() - started

        elapsed = asyncio.run(scenario())
        # The old rule imposed 60/30 = 2s here.
        self.assertLess(elapsed, 0.5, f"consecutive calls were spaced ({elapsed:.2f}s)")

    def test_budget_is_still_enforced_once_exhausted(self):
        """Bursting must not mean the quota is ignored."""
        async def scenario():
            p = profile(rpm=3)
            for _ in range(3):
                await p.wait_if_needed()
            # Budget spent; the next call must be told to wait.
            return p.seconds_until_ready()

        wait = asyncio.run(scenario())
        self.assertGreater(wait, 0.0)
        self.assertLessEqual(wait, 60.0)


class TestConcurrencyGate(unittest.TestCase):
    def test_limiter_caps_simultaneous_in_flight_calls(self):
        async def scenario():
            p = profile(rpm=600, concurrency=3)
            peak = 0
            current = 0

            async def worker():
                nonlocal peak, current
                await p.wait_if_needed()
                async with p.limiter():
                    current += 1
                    peak = max(peak, current)
                    await asyncio.sleep(0.02)
                    current -= 1

            await asyncio.gather(*(worker() for _ in range(12)))
            return peak

        self.assertEqual(asyncio.run(scenario()), 3)

    def test_limiter_allows_the_configured_parallelism(self):
        """A cap of 8 must actually run 8 at once, not one at a time."""
        async def scenario():
            p = profile(rpm=600, concurrency=8)
            started = time.monotonic()

            async def worker():
                await p.wait_if_needed()
                async with p.limiter():
                    await asyncio.sleep(0.1)

            await asyncio.gather(*(worker() for _ in range(8)))
            return time.monotonic() - started

        elapsed = asyncio.run(scenario())
        # Serial execution would be 8 x 0.1 = 0.8s.
        self.assertLess(elapsed, 0.4, f"calls did not run in parallel ({elapsed:.2f}s)")


class TestLockIsNotHeldWhileWaiting(unittest.TestCase):
    def test_a_waiting_caller_does_not_block_a_budgeted_one(self):
        """The regression that made concurrency unreachable.

        The old implementation slept inside the lock, so every caller queued
        behind whichever one was waiting out the budget.
        """
        async def scenario():
            p = profile(rpm=2)
            await p.wait_if_needed()
            await p.wait_if_needed()          # budget now exhausted

            blocked = asyncio.create_task(p.wait_if_needed())
            await asyncio.sleep(0.05)         # let it start waiting

            fresh = profile(rpm=60)
            started = time.monotonic()
            await fresh.wait_if_needed()
            elapsed = time.monotonic() - started

            blocked.cancel()
            return elapsed

        self.assertLess(asyncio.run(scenario()), 0.2)


class TestAdaptiveBackoffOnRateLimit(unittest.TestCase):
    """A 429 must tighten the shared window, not just the caller that saw it.

    Before ``note_rate_limited`` existed, ``wait_if_needed`` only consulted
    ``_call_times`` — a list of calls that *started*, unaffected by whether
    the endpoint then refused them. So one caller backing off in isolation
    left the window telling every other caller budget was still available,
    which is exactly how a benchmark run lost 6/46 calls: concurrent callers
    kept getting admitted straight into an endpoint that was already
    answering 429.
    """

    def test_rate_limit_blocks_other_callers_not_just_the_one_that_saw_it(self):
        async def scenario():
            p = profile(rpm=600)  # budget itself is not the constraint here
            await p.wait_if_needed()  # first caller gets in for free

            # The first caller's request comes back 429. It tells the shared
            # profile to back off for 0.3s.
            p.note_rate_limited(0.3)

            # A second, unrelated caller asks for budget immediately after.
            # Under the old code this returns instantly, because nothing
            # about the 429 was ever recorded anywhere the window could see.
            started = time.monotonic()
            await p.wait_if_needed()
            return time.monotonic() - started

        elapsed = asyncio.run(scenario())
        self.assertGreater(
            elapsed, 0.2,
            f"a 429 on one caller did not throttle a second caller ({elapsed:.2f}s) "
            "— the window is not adaptive",
        )

    def test_a_later_call_is_not_blocked_forever(self):
        """The block is a bounded deadline, not a permanent trip."""
        async def scenario():
            p = profile(rpm=600)
            p.note_rate_limited(0.1)
            await asyncio.sleep(0.15)
            started = time.monotonic()
            await p.wait_if_needed()
            return time.monotonic() - started

        elapsed = asyncio.run(scenario())
        self.assertLess(elapsed, 0.1, f"block outlived its hint ({elapsed:.2f}s)")


if __name__ == "__main__":
    unittest.main()


class TestRetryLayering(unittest.TestCase):
    """The provider SDK must not retry behind the rate limiter's back.

    `AsyncOpenAI` retries 429s internally by default. Those retries bypass
    `wait_if_needed` and `limiter`, so the rolling-minute budget cannot see
    them — and layered under this module's own five attempts, one logical call
    could issue up to fifteen requests against an endpoint already answering
    429. Retrying harder into a rate limit produces more rate limiting, and
    the amplification is invisible in our logs because it happens below them.
    """

    def test_client_delegates_all_retrying_to_this_module(self):
        from aegis.server.intent_parser import OpenAICompatibleProvider

        provider = OpenAICompatibleProvider(
            base_url="https://example.invalid/v1", api_key="k", model="m",
        )
        self.assertEqual(provider.client.max_retries, 0)
