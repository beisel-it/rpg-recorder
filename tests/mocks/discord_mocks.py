"""
discord_mocks.py — Mock objects for Discord / voice_recv without a real connection.

Usage (via conftest fixtures):
    def test_something(mock_voice_client, mock_bot):
        mock_voice_client.set_connected(True)
        assert mock_voice_client.is_connected()
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock


class MockVoiceData:
    """Minimal stand-in for voice_recv.VoiceData."""

    def __init__(self, pcm: bytes) -> None:
        self.pcm = pcm
        self.opus = b""  # unused by ChunkedFileSink when wants_opus=False


class MockUser:
    """Minimal stand-in for discord.User / discord.Member."""

    def __init__(self, user_id: int = 1001, name: str = "TestUser") -> None:
        self.id = user_id
        self.name = name
        self.display_name = name


class MockVoiceClient:
    """
    Simulates discord.VoiceClient / voice_recv.VoiceRecvClient without a real
    Discord connection.

    Control surface:
        vc.set_connected(True/False)   — changes is_connected() return value
        vc.fire_audio(user, pcm)       — calls the registered sink's write()
        vc.simulate_disconnect()       — sets connected=False (watchdog trigger)
    """

    def __init__(self) -> None:
        self._connected: bool = True
        self._sink: Any | None = None

    # --- voice_recv.VoiceRecvClient interface ---

    def is_connected(self) -> bool:
        return self._connected

    def listen(self, sink: Any) -> None:
        self._sink = sink

    def stop_listening(self) -> None:
        self._sink = None

    async def disconnect(self, *, force: bool = False) -> None:
        self._connected = False

    # --- Test helpers ---

    def set_connected(self, state: bool) -> None:
        """Manually set connection state (controllable in tests)."""
        self._connected = state

    def fire_audio(self, user: MockUser, pcm: bytes) -> None:
        """Push a PCM chunk into the registered sink's write() method."""
        if self._sink is None:
            raise RuntimeError("No sink registered — call listen() first")
        data = MockVoiceData(pcm)
        self._sink.write(user, data)

    def simulate_disconnect(self) -> None:
        """Trigger a disconnect (for watchdog tests)."""
        self._connected = False


class MockVoiceChannel:
    """Minimal stand-in for discord.VoiceChannel."""

    def __init__(self, name: str = "game-table") -> None:
        self.name = name
        self._vc = MockVoiceClient()
        self.last_connect_cls: Any = None  # tracks cls= passed to connect()

    async def connect(self, *, cls: Any = None, **kwargs: Any) -> MockVoiceClient:
        self.last_connect_cls = cls
        self._vc.set_connected(True)
        return self._vc


class MockInteraction:
    """
    Simulates discord.Interaction for slash-command tests.

    response.send_message() and followup.send() are captured so tests can
    assert on what the bot replied with.
    """

    def __init__(
        self,
        guild_id: int = 9999,
        user_id: int = 1001,
        voice_channel: MockVoiceChannel | None = None,
    ) -> None:
        self.guild_id = guild_id

        # Mimic interaction.user
        self.user = MockUser(user_id)

        # Mimic interaction.guild
        _voice_state = MagicMock()
        _voice_state.channel = voice_channel or MockVoiceChannel()
        _member = MagicMock()
        _member.voice = _voice_state
        _guild = MagicMock()
        _guild.get_member = MagicMock(return_value=_member)
        self.guild = _guild

        # Capture sent messages
        self.sent_messages: list[str] = []

        # response / followup objects
        self.response = _MockResponse(self.sent_messages)
        self.followup = _MockFollowup(self.sent_messages)

    def last_reply(self) -> str:
        """Return the most recent message sent to the user."""
        return self.sent_messages[-1] if self.sent_messages else ""


class _MockResponse:
    def __init__(self, capture: list[str]) -> None:
        self._capture = capture

    async def defer(self, *, ephemeral: bool = False, thinking: bool = False) -> None:
        pass

    async def send_message(self, content: str, *, ephemeral: bool = False) -> None:
        self._capture.append(content)


class _MockFollowup:
    def __init__(self, capture: list[str]) -> None:
        self._capture = capture

    async def send(self, content: str, **kwargs: Any) -> None:
        self._capture.append(content)


class MockBot:
    """
    Minimal discord.Bot / commands.Bot stand-in.

    Tracks registered cogs and dispatched events for assertion.
    """

    def __init__(self) -> None:
        self._cogs: dict[str, Any] = {}
        self.dispatched_events: list[tuple[str, Any]] = []

    def add_cog(self, cog: Any) -> None:
        self._cogs[type(cog).__name__] = cog

    def get_cog(self, name: str) -> Any | None:
        return self._cogs.get(name)

    def dispatch(self, event_name: str, *args: Any) -> None:
        self.dispatched_events.append((event_name, args))
