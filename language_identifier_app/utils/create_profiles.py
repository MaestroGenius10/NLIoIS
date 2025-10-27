import json
from pathlib import Path
from language_identifier_app.models import LanguageProfile


def create_language_profiles():
    base_dir = Path(__file__).resolve().parent
    ru_path = base_dir / "ru_corpus.json"
    de_path = base_dir / "de_corpus.json"


    with open(ru_path, encoding='utf-8') as f:
        ru_words = json.load(f)
    ru_short_words = {k: v for k, v in ru_words.items() if len(k) <= 5}

    LanguageProfile.objects.update_or_create(
        language='ru',
        defaults={
            'word_frequencies': ru_words,
            'short_word_frequencies': ru_short_words,
        }
    )

    with open(de_path, encoding='utf-8') as f:
        de_words = json.load(f)
    de_short_words = {k: v for k, v in de_words.items() if len(k) <= 5}

    LanguageProfile.objects.update_or_create(
        language='de',
        defaults={
            'word_frequencies': de_words,
            'short_word_frequencies': de_short_words,
        }
    )

    print("Профили русского и немецкого языков успешно созданы из JSON-корпуса!")
