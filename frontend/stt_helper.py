"""
Voice helper for SCIAS.

- transcribe_wav(): speech-to-text. Tries Google's online STT first (real
  Urdu support via ur-PK), falls back to offline Vosk if there's no
  internet connection.
- speak_text(): text-to-speech. Tries gTTS first (online), falls back to
  offline pyttsx3 if there's no internet connection.
"""

import json
import wave
from pathlib import Path

from vosk import Model, KaldiRecognizer
import pyttsx3
from gtts import gTTS
import speech_recognition as sr

MODEL_PATH = Path(__file__).parent.parent / "models" / "vosk-model-small-hi-0.22"

_model = None

GTTS_LANG_MAP = {
    "en": "en",
    "ur": "ur",
    "pa": "pa",
}

# Google STT uses locale-style codes, not plain ISO codes.
GOOGLE_STT_LANG_MAP = {
    "en": "en-US",
    "ur": "ur-PK",
    "pa": "pa-IN",
}


def get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Vosk model not found at {MODEL_PATH}")
        _model = Model(str(MODEL_PATH))
    return _model


def _transcribe_vosk(wav_path: str) -> str:
    """Offline fallback: mono 16-bit PCM WAV -> text, via Vosk."""
    wf = wave.open(wav_path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
        raise ValueError("Audio must be mono 16-bit PCM WAV")

    rec = KaldiRecognizer(get_model(), wf.getframerate())
    rec.SetWords(True)

    result_text = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result_text.append(json.loads(rec.Result()).get("text", ""))
    result_text.append(json.loads(rec.FinalResult()).get("text", ""))

    return " ".join(t for t in result_text if t).strip()


def transcribe_wav(wav_path: str, lang: str = "ur") -> str:
    """
    Transcribes a WAV file to text.

    Tries Google's online STT first (proper Urdu/Punjabi accuracy), falls
    back to offline Vosk (Hindi model only) if there's no internet or the
    Google service fails.
    """
    google_lang = GOOGLE_STT_LANG_MAP.get(lang, "ur-PK")
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language=google_lang)
        print(f"[stt_helper] Google STT SUCCESS (lang={google_lang}): '{text}'")
        return text
    except Exception as e:
        print(f"[stt_helper] Google STT FAILED (lang={google_lang}): {type(e).__name__}: {e}")
        print("[stt_helper] Falling back to offline Vosk (Hindi model)...")
        fallback_text = _transcribe_vosk(wav_path)
        print(f"[stt_helper] Vosk fallback result: '{fallback_text}'")
        return fallback_text


def speak_text(text: str, output_path: str = "temp_output", lang: str = "en") -> str:
    """
    Converts text to speech and saves it to disk.

    Tries gTTS (online) first, falls back to offline pyttsx3 if there's no
    internet. Returns the path actually written (.mp3 for gTTS, .wav for
    pyttsx3) — always use the returned path rather than assuming one.
    """
    gtts_lang = GTTS_LANG_MAP.get(lang, "en")
    try:
        mp3_path = f"{output_path}.mp3"
        tts = gTTS(text=text, lang=gtts_lang)
        tts.save(mp3_path)
        print(f"[speak_text] gTTS SUCCESS, lang={gtts_lang}")
        return mp3_path
    except Exception as e:
        print(f"[speak_text] gTTS FAILED (lang={gtts_lang}): {type(e).__name__}: {e}")
        wav_path = f"{output_path}.wav"
        engine = pyttsx3.init()
        engine.save_to_file(text, wav_path)
        engine.runAndWait()
        return wav_path