"""
AEGIS AI Provider Configuration.

Centralises API keys, endpoints, model lists, and rate-limit throttling
so any provider can be swapped without touching application code.
"""
import os
import time
import asyncio
import logging
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider profiles — add a new entry to support another backend
# ---------------------------------------------------------------------------
@dataclass
class ProviderProfile:
    """Rate-limit & connection settings for one LLM provider."""
    url: str
    api_key: str
    api_type: str               # "openai" (OpenAI-compatible) | "ollama"
    rpm: int = 30               # requests per minute
    rpd: int = 14400            # requests per day
    tpm: int = 6000             # tokens per minute (unused for now)
    # internal state
    _call_times: list = field(default_factory=list, repr=False)
    _lock: asyncio.Lock = field(default=None, init=False, repr=False)

    def seconds_until_ready(self) -> float:
        """Returns how many seconds to wait before the next call is safe."""
        now = time.monotonic()
        # Purge calls older than 60 s
        self._call_times = [t for t in self._call_times if now - t < 60.0]
        # Minimum inter-call gap: 60/rpm seconds (e.g. 2.4s at 25 RPM)
        min_gap = 60.0 / self.rpm
        if self._call_times:
            since_last = now - self._call_times[-1]
            if since_last < min_gap:
                return min_gap - since_last
        if len(self._call_times) < self.rpm:
            return 0.0
        # Must wait until the oldest call in the window expires
        oldest = self._call_times[0]
        return max(0.0, 60.0 - (now - oldest))

    def record_call(self):
        """Record that a call was just made."""
        self._call_times.append(time.monotonic())

    async def wait_if_needed(self):
        """Async helper — sleeps until RPM budget is available."""
        if self._lock is None:
            self._lock = asyncio.Lock()
        async with self._lock:
            wait = self.seconds_until_ready()
            if wait > 0:
                logger.info(f"Rate-limit throttle: waiting {wait:.1f}s")
                await asyncio.sleep(wait)
            self.record_call()


# ---------------------------------------------------------------------------
# Concrete provider instances
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    logger.warning(
        "GROQ_API_KEY not set. Set the environment variable before running."
    )

GROQ = ProviderProfile(
    url="https://api.groq.com/openai/v1/chat/completions",
    api_key=GROQ_API_KEY,
    api_type="openai",
    rpm=15,          # Safe for free-tier (4s gap between calls)
    rpd=14400,
    tpm=6000,
)

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA = ProviderProfile(
    url=os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat"),
    api_key=OLLAMA_API_KEY,
    api_type="ollama",
    rpm=60,          # Self-hosted — no hard limit
    rpd=999999,
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
    """Returns the ProviderProfile for a model, with fuzzy fallback."""
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
