"""
Speech-to-text agent for SCIAS.

Tries Groq's hosted Whisper endpoint first (best accuracy, single API call,
no local model/GPU needed). Falls back to Vosk if Groq fails (network issue,
rate limit, missing API key) -- Vosk runs fully offline once a language
model is downloaded, so it keeps the pipeline working without internet
or an API key, at the cost of lower accuracy.

Vosk requires mono 16kHz PCM WAV input. Non-WAV files (mp3, m4a, etc.)
are converted automatically via pydub before being passed to Vosk.
"""

import os
import json
import wave
from groq import Groq

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Map our language codes to local Vosk model folders.
# Download models from https://alphacephei.com/vosk/models and place them
# under models/, e.g. models/vosk-model-ur, models/vosk-model-small-en-us-0.15
VOSK_MODEL_PATHS = {
    "ur": "models/vosk-model-ur",
    "en": "models/vosk-model-small-en-us-0.15",
    # No dedicated Punjabi model is commonly available -- Urdu model used
    # as the closest practical substitute, same compromise as the TTS agent.
    "pa": "models/vosk-model-ur",
}

_vosk_models = {}  # cache loaded models per language so we don't reload every call


def _load_vosk_model(language: str):
    from vosk import Model

    model_path = VOSK_MODEL_PATHS.get(language, VOSK_MODEL_PATHS["en"])

    if model_path in _vosk_models:
        return _vosk_models[model_path]

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Vosk model not found at '{model_path}'. "
            f"Download it from https://alphacephei.com/vosk/models and extract it there."
        )

    model = Model(model_path)
    _vosk_models[model_path] = model
    return model


def _ensure_wav_mono_16k(audio_file_path: str) -> str:
    """Vosk needs mono 16kHz PCM WAV. Converts if the input isn't already in that format."""
    from pydub import AudioSegment

    audio = AudioSegment.from_file(audio_file_path)
    if audio.channels == 1 and audio.frame_rate == 16000 and audio_file_path.lower().endswith(".wav"):
        return audio_file_path

    converted_path = os.path.splitext(audio_file_path)[0] + "_16k_mono.wav"
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(converted_path, format="wav")
    return converted_path

VOSK_MODEL_PATHS = {
    "ur": "models/vosk-model-small-hi-0.22",
    "en": "models/vosk-model-small-en-us-0.15",  # you'd need to download this too if you want English fallback
    "pa": "models/vosk-model-small-hi-0.22",
}

def _transcribe_with_vosk(audio_file_path: str, language_hint: str = None) -> dict:
    try:
        from vosk import KaldiRecognizer

        language = language_hint or "en"
        model = _load_vosk_model(language)

        wav_path = _ensure_wav_mono_16k(audio_file_path)

        wf = wave.open(wav_path, "rb")
        recognizer = KaldiRecognizer(model, wf.getframerate())
        recognizer.SetWords(True)

        result_text = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                part = json.loads(recognizer.Result())
                result_text.append(part.get("text", ""))

        final_part = json.loads(recognizer.FinalResult())
        result_text.append(final_part.get("text", ""))
        wf.close()

        full_text = " ".join(t for t in result_text if t).strip()

        return {"text": full_text, "detected_language": language, "error": None}

    except Exception as e:
        return {"text": "", "detected_language": None, "error": str(e)}


def transcribe_audio(audio_file_path: str, language_hint: str = None) -> dict:
    """
    Transcribes an audio file (wav/mp3/m4a/etc.), trying Groq Whisper first
    and falling back to Vosk (offline) if Groq fails.

    Args:
        audio_file_path: path to the recorded audio file.
        language_hint: optional ISO 639-1 code (e.g. "ur", "pa", "en") to bias
            transcription accuracy if you already know/expect the language.
            Whisper auto-detects if omitted, but a hint helps with Punjabi,
            which Whisper can sometimes confuse with Urdu or Hindi. Vosk
            requires this hint to pick the right local model.

    Returns:
        {"text": str, "detected_language": str, "engine_used": str, "error": str | None}
    """
    try:
        with open(audio_file_path, "rb") as f:
            kwargs = {
                "file": (os.path.basename(audio_file_path), f.read()),
                "model": "whisper-large-v3",
                "response_format": "verbose_json",  # gives us detected language too
            }
            if language_hint:
                kwargs["language"] = language_hint

            transcription = groq_client.audio.transcriptions.create(**kwargs)

        return {
            "text": transcription.text.strip(),
            "detected_language": getattr(transcription, "language", None),
            "engine_used": "groq_whisper",
            "error": None,
        }

    except Exception as e:
        print(f"Groq Whisper transcription failed, falling back to Vosk. ({e})")
        vosk_result = _transcribe_with_vosk(audio_file_path, language_hint)
        vosk_result["engine_used"] = "vosk" if not vosk_result["error"] else None
        return vosk_result


if __name__ == "__main__":
    # Quick manual test:
    # 1. Put a sample .wav/.mp3 file of Urdu or Punjabi speech in this folder
    # 2. Update the path below and run: python agents/stt_agent.py
    test_file = "sample_audio/urdu_test.wav"
    if os.path.exists(test_file):
        result = transcribe_audio(test_file, language_hint="ur")
        print("Transcribed text:", result["text"])
        print("Detected language:", result["detected_language"])
        print("Engine used:", result["engine_used"])
        if result["error"]:
            print("Error:", result["error"])
    else:
        print(f"No test file found at {test_file}. Add a sample audio file to test.")