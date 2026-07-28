import importlib.util
import sys
import types
from pathlib import Path


AUTH_MODULE_PATH = Path(__file__).resolve().parents[1] / "channels" / "auth.py"


def load_auth_module(monkeypatch, gateway_url=""):
    config_module = types.ModuleType("config")
    config_module.config_get_by_key = (
        lambda key, default=None: gateway_url if key == "GATEWAY_URL" else default
    )
    monkeypatch.setitem(sys.modules, "config", config_module)

    spec = importlib.util.spec_from_file_location("channel_auth_under_test", AUTH_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_standalone_auth_rejects_wrong_secret(monkeypatch):
    monkeypatch.setenv("OMEGACLAW_AUTH_SECRET", "1234")
    auth = load_auth_module(monkeypatch)

    assert auth.is_auth_enabled() is True
    assert auth.verify_token("9999") is False
    assert auth.verify_token("1234") is True


def test_standalone_auth_without_secret_is_disabled_and_denies(monkeypatch):
    monkeypatch.delenv("OMEGACLAW_AUTH_SECRET", raising=False)
    auth = load_auth_module(monkeypatch)

    assert auth.is_auth_enabled() is False
    assert auth.verify_token("anything") is False
