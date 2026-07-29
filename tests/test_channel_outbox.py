import importlib.util
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CHANNELS_DIR = REPO_ROOT / "channels"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(CHANNELS_DIR) not in sys.path:
    sys.path.insert(0, str(CHANNELS_DIR))

from delivery_queue import PendingMessages


def _load_channel(name):
    spec = importlib.util.spec_from_file_location(
        f"{name}_outbox_test",
        CHANNELS_DIR / f"{name}.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module._outbox.clear()
    return module


def test_pending_messages_preserves_order_and_failed_head():
    outbox = PendingMessages()
    outbox.extend(["first", "second", "third"])
    delivered = []
    fail_second = True

    def deliver(message):
        nonlocal fail_second
        if message == "second" and fail_second:
            fail_second = False
            raise RuntimeError("temporary outage")
        delivered.append(message)

    with pytest.raises(RuntimeError, match="temporary outage"):
        outbox.flush(deliver)

    assert delivered == ["first"]
    assert len(outbox) == 2

    outbox.flush(deliver)

    assert delivered == ["first", "second", "third"]
    assert len(outbox) == 0


def test_pending_messages_waits_until_ready():
    outbox = PendingMessages()
    outbox.put("pending")
    delivered = []

    outbox.flush(delivered.append, ready=lambda: False)

    assert delivered == []
    assert len(outbox) == 1


def test_irc_buffers_until_connected(monkeypatch):
    irc = _load_channel("irc")
    irc._connected = False
    irc._channel = "#test"
    delivered = []
    monkeypatch.setattr(irc, "_deliver_outbound", delivered.append)

    irc.send_message("first")
    irc.send_message("second")
    assert len(irc._outbox) == 2

    irc._connected = True
    irc._flush_outbox()

    assert delivered == ["first", "second"]
    assert len(irc._outbox) == 0


def test_telegram_buffers_until_poll_connection(monkeypatch):
    telegram = _load_channel("telegram")
    telegram._connected = False
    telegram._chat_id = "chat-1"
    delivered = []
    monkeypatch.setattr(telegram, "_deliver_outbound", delivered.append)

    telegram.send_message("first")
    telegram.send_message("second")
    assert len(telegram._outbox) == 2

    telegram._connected = True
    telegram._flush_outbox()

    assert delivered == ["first", "second"]
    assert len(telegram._outbox) == 0


def test_mattermost_buffers_until_websocket_connection(monkeypatch):
    mattermost = _load_channel("mattermost")
    mattermost._connected = False
    mattermost.CHANNEL_ID = "channel-1"
    delivered = []
    monkeypatch.setattr(mattermost, "_deliver_outbound", delivered.append)

    mattermost.send_message("first")
    mattermost.send_message("second")
    assert len(mattermost._outbox) == 2

    mattermost._connected = True
    mattermost._flush_outbox()

    assert delivered == ["first", "second"]
    assert len(mattermost._outbox) == 0


def test_slack_buffers_until_channel_is_bound(monkeypatch):
    slack = _load_channel("slack")
    slack._bot_token = "token"
    slack._channel_id = ""
    delivered = []
    monkeypatch.setattr(slack, "_deliver_outbound", delivered.append)

    slack.send_message("first")
    slack.send_message("second")
    assert len(slack._outbox) == 2

    slack._channel_id = "channel-1"
    slack._flush_outbox()

    assert delivered == ["first", "second"]
    assert len(slack._outbox) == 0


@pytest.mark.parametrize("channel_name, loop_name, session_name", [
    ("irc", "_irc_loop", "_irc_session"),
    ("mattermost", "_ws_loop", "_ws_session"),
])
def test_disconnected_channels_reconnect(
    monkeypatch,
    channel_name,
    loop_name,
    session_name,
):
    channel = _load_channel(channel_name)
    channel._running = True
    attempts = []

    def session(*_args):
        attempts.append(True)
        if len(attempts) == 1:
            raise ConnectionError("temporary outage")
        channel._running = False

    monkeypatch.setattr(channel, session_name, session)
    monkeypatch.setattr(channel.time, "sleep", lambda _seconds: None)

    if channel_name == "irc":
        getattr(channel, loop_name)("#test", "server", 6667, "nick")
    else:
        getattr(channel, loop_name)()

    assert len(attempts) == 2
