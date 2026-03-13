"""
conftest.py (root) — Install lightweight discord stubs before any test imports.

discord.py and discord-ext-voice-recv are not required at test time.  We
inject minimal stub modules into sys.modules so that:

  from bot.cog      import RecordCog        # works
  from bot.recorder import ChunkedFileSink  # works

without a real discord installation.  The stubs expose only the symbols that
the production code references; they do *not* implement any behaviour.
"""

from __future__ import annotations
import os
os.environ.setdefault("DISCORD_TOKEN", "test-token-ci")
os.environ.setdefault("SESSIONS_DIR", "/tmp/rpg-test-sessions")

# Stub heavy ML/audio packages so transcribe.py tests work without real installs
import sys
from unittest.mock import MagicMock
import numpy as _np_real  # may fail — stub if missing
if "faster_whisper" not in sys.modules:
    sys.modules["faster_whisper"] = MagicMock()
sys.modules["faster_whisper"].WhisperModel = MagicMock
# soundfile.read must return a real array-like + sample_rate
# so that audio.ndim, len(audio), audio.mean() etc. work in transcribe.py
class _FakeAudio:
    """Minimal numpy array stub: 1D float32, 48000 samples (1 second)."""
    ndim = 1
    shape = (48000,)
    dtype = "float32"
    def __len__(self): return 48000
    size = 48000
    def mean(self, axis=None): return _FakeAudio()
    def __getitem__(self, key): return _FakeAudio()
    def reshape(self, *a, **kw): return self
    def astype(self, *a, **kw): return self

if "soundfile" not in sys.modules:
    _sf_mock = MagicMock()
    _sf_mock.read = MagicMock(return_value=(_FakeAudio(), 48000))
    sys.modules["soundfile"] = _sf_mock

# numpy: use real if available, else stub
try:
    import numpy  # noqa: F401
except ModuleNotFoundError:
    sys.modules["numpy"] = MagicMock()


import sys
import types
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Build stub modules
# ---------------------------------------------------------------------------

def _stub_module(name: str, **attrs) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__spec__ = None  # suppress "spec is None" warnings
    for k, v in attrs.items():
        setattr(mod, k, v)
    return mod


# ── discord.Interaction, Member, User, VoiceChannel ─────────────────────────

class _Interaction:
    pass


class _Member:
    pass


class _User:
    pass


class _VoiceChannel:
    pass


# ── discord.app_commands ─────────────────────────────────────────────────────

def _app_command_decorator(*args, **kwargs):
    """Return a no-op decorator for @app_commands.command(...)."""
    def decorator(func):
        return func
    return decorator


class _Group:
    """Stub for discord.app_commands.Group that supports @group.command(...)."""

    def __init__(self, *, name: str = "", description: str = "", **kw):
        self.name = name
        self.description = description
        self._commands: dict[str, object] = {}

    def command(self, *, name: str = "", description: str = "", **kw):
        """Register a coroutine as a sub-command and expose it by name."""
        def decorator(func):
            # Make the function callable via .callback so tests can reach it:
            #   await cog.record_start.callback(cog, interaction)
            cmd = _AppCommand(name=name or func.__name__, callback=func)
            self._commands[cmd.name] = cmd
            return cmd
        return decorator


class _AppCommand:
    """Minimal slash-command stub."""

    def __init__(self, *, name: str, callback) -> None:
        self.name = name
        self.callback = callback

    async def __call__(self, *args, **kwargs):
        return await self.callback(*args, **kwargs)


_app_commands_mod = _stub_module(
    "discord.app_commands",
    Group=_Group,
    command=_app_command_decorator,
)


# ── discord.ext.commands ─────────────────────────────────────────────────────

class _Cog:
    """Minimal commands.Cog stub; subclasses just need to exist."""
    pass


class _Bot:
    pass


_commands_mod = _stub_module(
    "discord.ext.commands",
    Cog=_Cog,
    Bot=_Bot,
)


# ── discord.ext.voice_recv ───────────────────────────────────────────────────

class _AudioSink:
    """Stub for voice_recv.AudioSink."""
    wants_opus: bool = False

    def write(self, user, data) -> None:
        pass

    def cleanup(self) -> None:
        pass


class _VoiceData:
    def __init__(self, pcm: bytes = b"") -> None:
        self.pcm = pcm
        self.opus = b""


class _VoiceRecvClient:
    pass


_voice_recv_mod = _stub_module(
    "discord.ext.voice_recv",
    AudioSink=_AudioSink,
    VoiceData=_VoiceData,
    VoiceRecvClient=_VoiceRecvClient,
)


# ── discord (top-level) ──────────────────────────────────────────────────────

_discord_mod = _stub_module(
    "discord",
    Interaction=_Interaction,
    Member=_Member,
    User=_User,
    VoiceChannel=_VoiceChannel,
    app_commands=_app_commands_mod,
)


# ── discord.ext (package) ────────────────────────────────────────────────────

_ext_mod = _stub_module("discord.ext")


# ---------------------------------------------------------------------------
# Inject into sys.modules before any test imports bot.*
# ---------------------------------------------------------------------------

_STUBS = {
    "discord":                   _discord_mod,
    "discord.app_commands":      _app_commands_mod,
    "discord.ext":               _ext_mod,
    "discord.ext.commands":      _commands_mod,
    "discord.ext.voice_recv":    _voice_recv_mod,
}

for _name, _mod in _STUBS.items():
    sys.modules.setdefault(_name, _mod)
