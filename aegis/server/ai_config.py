"""
AEGIS AI Provider Configuration.

Centralises API keys, endpoints, model lists, and rate-limit throttling
so any provider can be swapped without touching application code.

Configure any OpenAI-compatible provider via environment variables:
  LLM_BASE_URL — e.g. https://api.groq.com/openai/v1
  LLM_API_KEY  — your provider's API key
  LLM_MODEL    — model name to use (default: llama-3.1-8b-instant)
"""
import os
import time
import asyncio
import logging
from dataclasses import dataclass, field
from typing import ClassVar
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider profiles — add a new entry to support another backend
# ---------------------------------------------------------------------------
@dataclass
class ProviderProfile:
    """Rate-limit, concurrency and connection settings for one LLM provider.

    Rate limiting and concurrency are deliberately separate concerns:

    * ``rpm`` bounds how many requests may *start* within any 60-second window.
      It protects the provider's quota.
    * ``concurrency`` bounds how many may be *in flight* simultaneously. It
      protects local resources and keeps a slow endpoint from queuing without
      limit.

    The previous implementation conflated them and, in doing so, made
    concurrency unreachable.  It enforced a minimum inter-call gap of
    ``60/rpm`` seconds — so at 30 RPM every call was spaced two seconds apart
    regardless of how many callers were waiting — and it slept *while holding
    the lock*, which serialised every caller behind the sleeper.  Raising a
    concurrency setting had no effect whatsoever: N concurrent requests still
    completed in N × 2 seconds.

    The window below permits genuine bursting up to ``rpm`` and only waits when
    the budget is actually exhausted.
    """
    url: str
    api_key: str
    api_type: str               # "openai" (OpenAI-compatible) | "ollama"
    rpm: int = 30               # requests that may start per rolling minute
    rpd: int = 14400            # requests per day
    tpm: int = 6000             # tokens per minute (unused for now)
    concurrency: int = 8        # requests allowed in flight at once
    # internal state
    _call_times: list = field(default_factory=list, repr=False)
    _lock: asyncio.Lock = field(default=None, init=False, repr=False)
    _semaphore: asyncio.Semaphore = field(default=None, init=False, repr=False)
    #: Upper bound on how long one observed refusal may hold back every caller.
    #: ClassVar, not a field: this is a policy constant, and annotating it as a
    #: plain attribute would make it a constructor argument of every profile.
    MAX_BACKOFF_SECONDS: ClassVar[float] = 60.0

    # Monotonic deadline set by note_rate_limited() when the endpoint itself
    # answers 429. Separate from _call_times: that list only records that a
    # call *started*, which a refusal does not undo, so without this the
    # rolling window kept admitting new calls at the same nominal rate right
    # through an active 429 storm.
    _blocked_until: float = field(default=0.0, init=False, repr=False)

    def seconds_until_ready(self) -> float:
        """Seconds to wait before another call may start.

        Returns ``0.0`` whenever the rolling-minute budget has room, so callers
        may burst up to ``rpm`` without artificial spacing.
        """
        now = time.monotonic()
        # Purge calls older than 60 s
        self._call_times = [t for t in self._call_times if now - t < 60.0]
        if len(self._call_times) < self.rpm:
            return 0.0
        # Budget exhausted — wait for the oldest call to age out of the window.
        oldest = self._call_times[0]
        return max(0.0, 60.0 - (now - oldest))

    def record_call(self):
        """Record that a call was just made."""
        self._call_times.append(time.monotonic())

    def note_rate_limited(self, wait_hint: float):
        """Feed an observed 429 back into the shared window.

        Before this existed, the rolling window only tracked how many calls
        *started* (``_call_times``); it had no way to learn that the endpoint
        just refused one. So while one caller ran its own isolated backoff,
        the window kept telling every other caller — including concurrent
        requests already in flight and new ones about to start — that budget
        was available, and they piled straight into the same refusal. That is
        the actual mechanism behind a benchmark run losing 6/46 calls to
        exhausted retries: three concurrent callers each independently waited
        10s, then 20s, then 30s, while the limiter admitted more requests
        underneath them the whole time.

        ``wait_hint`` should be the caller's own backoff for this attempt
        (ideally derived from a ``Retry-After`` header, since that is the
        endpoint's own word on how long it needs — see
        ``intent_parser._retry_after_seconds``). Every other caller is now
        blocked for at least that long too, so the window's admission rate is
        actually driven by what the endpoint just did, not by a fixed local
        guess.
        """
        # Capped, because this deadline is set from a value the endpoint
        # supplies. An oversized Retry-After — or a stream of them stacking —
        # would otherwise park every caller in the process behind one server's
        # word for minutes, converting a slow endpoint into a total stall and
        # turning a recoverable degradation into a dead pipeline. The cap keeps
        # the signal useful while bounding how much damage one bad response can
        # do; a genuinely longer outage simply produces a second block.
        wait = min(max(0.0, wait_hint), self.MAX_BACKOFF_SECONDS)
        self._blocked_until = max(self._blocked_until, time.monotonic() + wait)

    def limiter(self) -> asyncio.Semaphore:
        """Concurrency gate for in-flight requests.

        Created lazily because a Semaphore binds to the running event loop.
        """
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(max(1, self.concurrency))
        return self._semaphore

    async def wait_if_needed(self, record: bool = True):
        """Block until the rolling-minute budget allows another call.

        The lock is held only for bookkeeping.  Sleeping happens *outside* it,
        so a caller waiting on budget does not block callers that still have
        budget — which is what previously reduced every concurrent run to a
        single serial queue.

        ``record`` exists because this has to be checked twice per call: once
        before queueing on the concurrency semaphore, and once after winning
        it. A caller can sit on that semaphore for an unbounded time, and
        another caller's 429 during the wait sets a block the winner would
        otherwise sail straight through — issuing a request into the window the
        endpoint had just closed. Only the second check consumes budget;
        counting both would spend the rolling window at twice the configured
        rate and throttle the run below its own ``rpm``.
        """
        if self._lock is None:
            self._lock = asyncio.Lock()

        while True:
            async with self._lock:
                now = time.monotonic()
                # Two independent reasons a call may have to wait: the
                # rolling budget is spent, or the endpoint has already told us
                # (via note_rate_limited) to back off regardless of budget.
                # Taking the max of the two is what makes a 429 actually
                # tighten admission instead of the window ignoring it.
                wait = max(self.seconds_until_ready(), self._blocked_until - now)
                if wait <= 0:
                    if record:
                        self.record_call()
                    return
            logger.debug("Rate-limit budget exhausted; waiting %.1fs", wait)
            await asyncio.sleep(wait)


# ---------------------------------------------------------------------------
# Concrete provider instances
# ---------------------------------------------------------------------------

# Generic OpenAI-compatible provider — configure via environment variables.
# Takes precedence over provider-specific keys when LLM_BASE_URL is set.
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_API_KEY  = os.getenv("LLM_API_KEY", "")
LLM_MODEL    = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

# Groq — kept for backward compatibility; used when LLM_BASE_URL is not set.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def _safe_int(val: str, default: int) -> int:
    return int(val) if val.isdigit() else default


GROQ = ProviderProfile(
    url="https://api.groq.com/openai/v1/chat/completions",
    api_key=GROQ_API_KEY,
    api_type="openai",
    rpm=_safe_int(os.getenv("LLM_RPM", "15"), 15),   # free tier is 15/min
    rpd=14400,
    tpm=6000,
    concurrency=_safe_int(os.getenv("LLM_CONCURRENCY", "4"), 4),
)

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA = ProviderProfile(
    url=os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat"),
    api_key=OLLAMA_API_KEY,
    api_type="ollama",
    rpm=_safe_int(os.getenv("LLM_RPM", "600"), 600),  # self-hosted, no quota
    rpd=999999,
    concurrency=_safe_int(os.getenv("LLM_CONCURRENCY", "16"), 16),
)

# Generic provider profile — resolved at startup from LLM_BASE_URL / LLM_API_KEY.
# rpm=30 is a safe default; override by setting LLM_RPM in your environment.
def _custom_url(base: str) -> str:
    """Build the full chat-completions URL from LLM_BASE_URL.

    Ensures /v1 is present before /chat/completions so that bare hostnames
    (e.g. https://omniroute.host.com) work the same as full base URLs
    (e.g. https://omniroute.host.com/v1).
    """
    base = base.rstrip("/")
    if not base.endswith("/v1") and "/v1/" not in base:
        base = base + "/v1"
    return base + "/chat/completions"

#: In-flight request cap. Raise it for a self-hosted gateway or a paid tier;
#: lower it if the provider starts returning 429s faster than the RPM window
#: predicts. This is independent of LLM_RPM — see ProviderProfile.
LLM_CONCURRENCY = _safe_int(os.getenv("LLM_CONCURRENCY", "8"), 8)

CUSTOM = ProviderProfile(
    # Store the full chat-completions URL so legacy httpx callers get a working endpoint.
    # OpenAICompatibleProvider strips /chat/completions itself before passing to the SDK.
    url=_custom_url(LLM_BASE_URL) if LLM_BASE_URL else GROQ.url,
    api_key=LLM_API_KEY or GROQ_API_KEY,
    api_type="openai",
    rpm=_safe_int(os.getenv("LLM_RPM", "60"), 60),
    rpd=_safe_int(os.getenv("LLM_RPD", "14400"), 14400),
    concurrency=LLM_CONCURRENCY,
)

# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------
GROQ_MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
OLLAMA_MODELS = ["gpt-oss:120b", "minimax-m2.5"]
DEFAULT_MODELS = GROQ_MODELS

# Map model name → provider profile
_MODEL_PROVIDERS: dict[str, ProviderProfile] = {}
for m in GROQ_MODELS:
    _MODEL_PROVIDERS[m] = GROQ
for m in OLLAMA_MODELS:
    _MODEL_PROVIDERS[m] = OLLAMA


def get_provider(model_name: str) -> ProviderProfile:
    """Returns the ProviderProfile for a model.

    When LLM_BASE_URL is configured, the generic CUSTOM provider is always
    returned so all calls go through the user-configured endpoint regardless
    of model name.
    """
    if LLM_BASE_URL:
        return CUSTOM
    if model_name in _MODEL_PROVIDERS:
        return _MODEL_PROVIDERS[model_name]
    lower = model_name.lower()
    if any(p in lower for p in ["llama", "mixtral", "gemma", "qwen"]):
        return GROQ
    return OLLAMA


def get_llm_config(model_name: str):
    """Legacy helper — returns (url, api_key, api_type)."""
    p = get_provider(model_name)
    return p.url, p.api_key, p.api_type


def _warn_missing_keys():
    """Emit a startup warning when no API key is configured."""
    if not LLM_API_KEY and not GROQ_API_KEY and not OLLAMA_API_KEY:
        logger.warning(
            "No LLM API key found. Set LLM_API_KEY (generic) or GROQ_API_KEY "
            "before running AEGIS."
        )

_warn_missing_keys()
