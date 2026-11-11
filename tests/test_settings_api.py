import pytest
from fastapi import HTTPException

from Tobi.config import settings
from Tobi.core import settings_api


@pytest.mark.parametrize("voice", ["af_heart", "en-US-AriaNeural"])
@pytest.mark.asyncio
async def test_update_tts_voice_writes_env_and_updates_runtime(tmp_path, monkeypatch, voice):
    monkeypatch.setattr(settings, "Tobi_HOME", tmp_path)
    monkeypatch.setattr(settings, "TTS_VOICE", "bf_emma")

    result = await settings_api.update_settings({"TTS_VOICE": voice})

    assert result["success"] is True
    assert result["updated"] == ["TTS_VOICE"]
    assert voice == settings.TTS_VOICE
    assert f"TTS_VOICE={voice}" in (tmp_path / ".env").read_text(encoding="utf-8")


@pytest.mark.parametrize("voice", ["", "bad voice", "voice;rm", "../../secrets", 12])
@pytest.mark.asyncio
async def test_update_tts_voice_rejects_invalid_identifiers(voice):
    with pytest.raises(HTTPException) as exc_info:
        await settings_api.update_settings({"TTS_VOICE": voice})

    assert exc_info.value.status_code == 400
    assert "valid voice identifier" in exc_info.value.detail
