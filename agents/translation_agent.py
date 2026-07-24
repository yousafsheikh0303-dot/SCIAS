"""
Translation agent for SCIAS.

Sits at two points in the pipeline:
  1. Entry: detect the farmer's language, translate their query to English
     before it hits the router/agents (which all assume English internally).
  2. Exit: translate the final English answer back into the farmer's
     original language before it's spoken/displayed.

Uses the Groq LLM directly rather than a separate translation API, so no
new credentials are needed and behavior is consistent with the rest of
the stack. Falls back safely to "assume English" if detection/translation
fails, so a translation-layer bug never blocks the whole pipeline.
"""

from langchain_groq import ChatGroq
from groq import RateLimitError

# Small, fast model -- translation/detection is a simple task, doesn't need 70B.
translation_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

SUPPORTED_LANGUAGES = {
    "en": "English",
    "ur": "Urdu",
    "pa": "Punjabi",
}


def detect_and_translate_to_english(text: str) -> dict:
    """
    Detects the input language and translates to English if needed.

    Returns:
        {
            "original_text": str,
            "detected_language": str,   # ISO code: en / ur / pa / other
            "english_text": str,        # ready to hand to the router
        }
    """
    prompt = f"""You are a language detection and translation tool for a Pakistani agricultural advisory app.

Given the farmer's message below, do two things:
1. Detect the language. Respond with ONLY one of these codes: en (English), ur (Urdu), pa (Punjabi), or other.
2. If the language is NOT English, translate the message to natural, simple English suitable for an agricultural assistant.

Important agricultural vocabulary — do not confuse these crop names:
- گندم (Urdu) / ਕਣਕ (Punjabi) = wheat
- چاول (Urdu) / ਚਾਵਲ (Punjabi) = rice
- کپاس (Urdu) / ਕਪਾਹ (Punjabi) = cotton
- گنا (Urdu) / ਗੰਨਾ (Punjabi) = sugarcane
- مکئی (Urdu) / ਮੱਕੀ (Punjabi) = maize / corn

Always translate crop names using the exact English term above when one of these words appears. Do not substitute a different crop.

Important weather vocabulary — "موسم" (mausam) can mean either "weather" or "season" in
Urdu, and "ਮੌਸਮ" works the same way in Punjabi. In this agricultural advisory context,
default to "weather" whenever موسم/ਮੌਸਮ appears together with a place name, a question
word (کیا/کیسا/کب), or words like بارش/rain, گرمی/heat, سردی/cold — these are asking
about current outdoor conditions, not a cropping season. Only use "season" when the
sentence is clearly about a growing/cropping period (e.g. mentions بوائی/sowing,
کٹائی/harvest, یا ربیع/kharif crop names directly).

Examples:
- "اسلام آباد کا موسم کیا ہے" -> "What is the weather in Islamabad?"
- "لاہور کا موسم کیسا ہے" -> "What is the weather like in Lahore?"
- "کیا موسم بارش کا ہے" -> "Is it raining?"
- "ربیع کا موسم" -> "the rabi season"
- "بوائی کا موسم" -> "the sowing season"

Respond in EXACTLY this format, nothing else:
LANGUAGE: <code>
TRANSLATION: <english text, or the original text unchanged if it was already English>

Farmer's message: {text}
"""

    try:
        result = translation_llm.invoke(prompt)
        content = result.content.strip()

        lang_code = "en"
        english_text = text

        for line in content.split("\n"):
            if line.upper().startswith("LANGUAGE:"):
                code = line.split(":", 1)[1].strip().lower()
                if code in SUPPORTED_LANGUAGES or code == "other":
                    lang_code = code
            elif line.upper().startswith("TRANSLATION:"):
                english_text = line.split(":", 1)[1].strip()

        # Safety net: if translation came back empty, fall back to original text
        if not english_text:
            english_text = text

        print(f"[translation_agent] lang={lang_code} | original='{text}' -> english='{english_text}'")

        return {
            "original_text": text,
            "detected_language": lang_code,
            "english_text": english_text,
        }

    except RateLimitError:
        # Quota hit -- fail safe by assuming English rather than blocking the pipeline
        return {"original_text": text, "detected_language": "en", "english_text": text}
    except Exception:
        return {"original_text": text, "detected_language": "en", "english_text": text}


def translate_from_english(english_answer: str, target_language: str) -> str:
    """
    Translates the final English answer back into the farmer's language.
    If target_language is 'en' or unrecognized, returns the answer unchanged.
    """
    if target_language == "en" or target_language not in SUPPORTED_LANGUAGES:
        return english_answer

    language_name = SUPPORTED_LANGUAGES[target_language]

    prompt = f"""Translate the following agricultural advisory answer into natural, simple {language_name}.
Respond ONLY in {language_name}, using {language_name}'s native script. Do not mix in any other language or script, and do not include parenthetical translations into other languages.
Keep numbers, prices, and dates clear. Do not add any commentary — output ONLY the translation, nothing else.

Crop name reference (use the {language_name} term only, do not show alternatives):
- wheat = {"گندم" if target_language == "ur" else "ਕਣਕ"}
- rice = {"چاول" if target_language == "ur" else "ਚਾਵਲ"}
- cotton = {"کپاس" if target_language == "ur" else "ਕਪਾਹ"}
- sugarcane = {"گنا" if target_language == "ur" else "ਗੰਨਾ"}
- maize / corn = {"مکئی" if target_language == "ur" else "ਮੱਕੀ"}

Answer to translate:
{english_answer}

{language_name} translation (only, no other language mixed in):"""

    try:
        result = translation_llm.invoke(prompt)
        translated = result.content.strip()
        return translated if translated else english_answer
    except RateLimitError:
        return english_answer
    except Exception:
        return english_answer