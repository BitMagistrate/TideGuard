import pytest

from tideguard_bot.main import Settings, _bbox_for_point, _safe_float


def test_settings_requires_token(monkeypatch):
    monkeypatch.delenv("TIDEGUARD_BOT_TOKEN", raising=False)
    with pytest.raises(SystemExit):
        Settings.from_env()


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("TIDEGUARD_BOT_TOKEN", "1234:abc")
    monkeypatch.setenv("TIDEGUARD_API_BASE", "https://api.example.com")
    settings = Settings.from_env()
    assert settings.token == "1234:abc"
    assert settings.api_base == "https://api.example.com"
    # Default bbox now points at the Black Sea (Anapa / Novorossiysk), not Taiwan.
    assert settings.default_bbox.startswith("37.")


def test_settings_default_bbox_override(monkeypatch):
    monkeypatch.setenv("TIDEGUARD_BOT_TOKEN", "1234:abc")
    monkeypatch.setenv("TIDEGUARD_BOT_DEFAULT_BBOX", "27,40,42,47")
    settings = Settings.from_env()
    assert settings.default_bbox == "27,40,42,47"


def test_safe_float() -> None:
    assert _safe_float("12.5") == 12.5
    assert _safe_float("nope") is None
    assert _safe_float("") is None


def test_bbox_for_point_centred_on_anapa() -> None:
    bbox = _bbox_for_point(44.9, 37.3, half_deg=0.5)
    lon_min, lat_min, lon_max, lat_max = (float(x) for x in bbox.split(","))
    assert lon_min < 37.3 < lon_max
    assert lat_min < 44.9 < lat_max
    assert pytest.approx(lon_max - lon_min, rel=1e-6) == 1.0
    assert pytest.approx(lat_max - lat_min, rel=1e-6) == 1.0
