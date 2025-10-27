import re
import json
import ollama  # Убедитесь, что библиотека установлена: pip install ollama


# -------------------------------------------------------------
# 1. Метод частотных слов (Метрика: процент известных слов)
# -------------------------------------------------------------
def detect_language_freq(text, language_profiles):
    words = re.findall(r'\b\w+\b', text.lower())

    if not words or not language_profiles:
        return 'ru', 0.0

    lang_scores = {}
    total_word_count = len(words)

    for profile in language_profiles:
        profile_freqs = profile.word_frequencies

        known_words_count = 0
        for word in words:
            if word in profile_freqs:
                known_words_count += 1

        score = known_words_count / total_word_count
        lang_scores[profile.language] = score

    if not lang_scores:
        return 'ru', 0.0

    best_lang = max(lang_scores, key=lang_scores.get)
    best_score = lang_scores[best_lang]

    return best_lang, best_score


# -------------------------------------------------------------
# 2. Метод коротких слов (Метрика: процент известных слов)
# -------------------------------------------------------------
def detect_language_short(text, language_profiles, max_len=5):

    all_words = re.findall(r'\b\w+\b', text.lower())
    words = [w for w in all_words if len(w) <= max_len]

    if not words or not language_profiles:
        return 'ru', 0.0

    lang_scores = {}
    total_word_count = len(words)

    for profile in language_profiles:
        profile_freqs = profile.short_word_frequencies

        known_words_count = 0
        for word in words:
            if word in profile_freqs:
                known_words_count += 1

        score = known_words_count / total_word_count
        lang_scores[profile.language] = score

    if not lang_scores:
        return 'ru', 0.0

    best_lang = max(lang_scores, key=lang_scores.get)
    best_score = lang_scores[best_lang]

    return best_lang, best_score


# -------------------------------------------------------------
# 3. Нейросетевой метод (через Ollama)
# -------------------------------------------------------------

import json
import ollama


def detect_language_neural_ollama(text, model_name='llama3'):
    if not text or not text.strip():
        return 'ru', 0.0

    prompt = f"""
    You are an expert language identifier. Your task is to identify the main language of the provided text.
    Your response MUST be a JSON object with two keys:
    1. "language_code": The two-letter ISO 639-1 code for the detected language (e.g., "ru", "de", "en").
    2. "confidence": A float between 0.0 and 1.0 indicating your confidence.

    Analyze the following text and provide your response in the specified JSON format only.
    Text: "{text}"
    """

    try:
        response = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            format='json'
        )

        response_content = response['message']['content']
        data = json.loads(response_content)

        lang_code = data.get('language_code', 'ru').strip().lower()
        confidence = float(data.get('confidence', 0.0))

        return lang_code, confidence

    except ollama.ResponseError as e:
        print(f"!!! Ошибка от сервера Ollama: {e.error}")
        print(f"!!! Убедитесь, что модель '{model_name}' скачана (команда: ollama pull {model_name})")
        return 'ru', 0.0
    except Exception as e:
        print(f"!!! Произошла ошибка при обращении к Ollama: {e}")
        print("!!! Убедитесь, что сервер Ollama запущен и доступен.")
        return 'ru', 0.0