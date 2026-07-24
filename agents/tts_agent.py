"""
Text-to-speech agent for SCIAS.

Tries Coqui TTS first (better quality, offline once models are downloaded).
Falls back to ElevenLabs if Coqui isn't available and an API key is set
(higher quality than gTTS, especially for Urdu).
Falls back to gTTS as the final option -- so a TTS environment problem
never blocks the voice pipeline end-to-end.

gTTS requires internet access (it calls Google Translate's TTS endpoint)
but has zero local setup and reliably supports Urdu ("ur"). Punjabi is not
directly supported by gTTS as of this writing -- see note in synthesize_speech.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# gTTS language codes for our supported languages.
# Punjabi has no dedicated gTTS code; "hi" (Hindi) or "ur" are the closest
# practical substitutes for the fallback path -- flagged clearly below since
# it's a real quality compromise, not a transparent equivalent.
GTTS_LANG_MAP = {
    "en": "en",
    "ur": "ur",
    "pa": "ur",  # fallback substitute -- gTTS has no native Punjabi voice
}

# ElevenLabs default voice IDs -- swap these for voices you prefer/clone later.
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # "Rachel"
ELEVENLABS_MODEL_ID = "eleven_multilingual_v2"  # needed for Urdu/Punjabi support

_coqui_tts_instance = None
_coqui_available = None  # cached after first check, so we don't retry import every call

_elevenlabs_client = None
_elevenlabs_available = None  # cached after first check


def _try_load_coqui():
    global _coqui_tts_instance, _coqui_available
    if _coqui_available is not None:
        return _coqui_available

    try:
        from TTS.api import TTS  # type: ignore
        # XTTS v2 is Coqui's multilingual model with the broadest language coverage,
        # including Urdu-adjacent languages. Punjabi is not in its supported list
        # either, so this mainly helps Urdu quality over gTTS.
        _coqui_tts_instance = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        _coqui_available = True
        print("Coqui TTS loaded successfully.")
    except Exception as e:
        print(f"Coqui TTS not available, will try ElevenLabs/gTTS fallback. ({e})")
        _coqui_available = False

    return _coqui_available


def _try_load_elevenlabs():
    global _elevenlabs_client, _elevenlabs_available
    if _elevenlabs_available is not None:
        return _elevenlabs_available

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ELEVENLABS_API_KEY not set, will use gTTS fallback.")
        _elevenlabs_available = False
        return _elevenlabs_available

    try:
        from elevenlabs.client import ElevenLabs
        _elevenlabs_client = ElevenLabs(api_key=api_key)
        _elevenlabs_available = True
        print("ElevenLabs client loaded successfully.")
    except Exception as e:
        print(f"ElevenLabs not available, will use gTTS fallback. ({e})")
        _elevenlabs_available = False

    return _elevenlabs_available


def _synthesize_with_coqui(text: str, language: str, output_path: str, speaker_wav: str = None) -> bool:
    """Returns True on success, False if it should fall back."""
    if not _try_load_coqui():
        return False

    try:
        # XTTS v2 requires a reference speaker wav for voice cloning.
        # Without one, use Coqui's built-in default speaker if the install provides it;
        # otherwise this will raise and we fall back.
        kwargs = {"text": text, "language": language if language in ("en", "ur") else "en", "file_path": output_path}
        if speaker_wav:
            kwargs["speaker_wav"] = speaker_wav
        _coqui_tts_instance.tts_to_file(**kwargs)
        return os.path.exists(output_path)
    except Exception as e:
        print(f"Coqui synthesis failed, falling back. ({e})")
        return False


def _synthesize_with_elevenlabs(text: str, output_path: str) -> bool:
    """Returns True on success, False if it should fall back to gTTS."""
    if not _try_load_elevenlabs():
        return False

    try:
        audio = _elevenlabs_client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            model_id=ELEVENLABS_MODEL_ID,
            text=text,
        )
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        return os.path.exists(output_path)
    except Exception as e:
        print(f"ElevenLabs synthesis failed, falling back to gTTS. ({e})")
        return False


def _synthesize_with_gtts(text: str, language: str, output_path: str) -> bool:
    try:
        from gtts import gTTS
        lang_code = GTTS_LANG_MAP.get(language, "en")
        tts = gTTS(text=text, lang=lang_code)
        tts.save(output_path)
        return os.path.exists(output_path)
    except Exception as e:
        print(f"gTTS synthesis also failed: {e}")
        return False


def synthesize_speech(text: str, language: str = "en", output_path: str = "output_audio.mp3",
                       speaker_wav: str = None) -> dict:
    """
    Converts text to speech, trying Coqui TTS, then ElevenLabs, then gTTS.

    Args:
        text: the text to speak (already translated into the target language).
        language: ISO code -- "en", "ur", or "pa".
        output_path: where to save the resulting audio file.
        speaker_wav: optional reference voice sample for Coqui voice cloning.

    Returns:
        {"output_path": str | None, "engine_used": "coqui" | "elevenlabs" | "gtts" | None, "error": str | None}
    """
    if _synthesize_with_coqui(text, language, output_path, speaker_wav):
        return {"output_path": output_path, "engine_used": "coqui", "error": None}

    if _synthesize_with_elevenlabs(text, output_path):
        return {"output_path": output_path, "engine_used": "elevenlabs", "error": None}

    if _synthesize_with_gtts(text, language, output_path):
        return {"output_path": output_path, "engine_used": "gtts", "error": None}

    return {"output_path": None, "engine_used": None, "error": "Coqui, ElevenLabs, and gTTS synthesis all failed."}


if __name__ == "__main__":
    # Quick manual test
    result = synthesize_speech(
        text="آپ کے گندم کے کھیت کو جلد پانی دینے کی ضرورت ہے۔",
        language="ur",
        output_path="test_output.mp3",
    )
    print(result)