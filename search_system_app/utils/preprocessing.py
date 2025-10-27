import re

# Попытка импортировать pymorphy2
try:
    import pymorphy2
    morph = pymorphy2.MorphAnalyzer()
    PYMORPHY_AVAILABLE = True
except ImportError:
    PYMORPHY_AVAILABLE = False

# Попытка импортировать стоп-слова nltk
try:
    from nltk.corpus import stopwords
    russian_stopwords = set(stopwords.words("russian"))
except (ImportError, LookupError):
    import nltk
    nltk.download('stopwords', quiet=True)
    try:
        from nltk.corpus import stopwords
        russian_stopwords = set(stopwords.words("russian"))
    except Exception:
        russian_stopwords = set()
        print("Предупреждение: не удалось загрузить стоп-слова.")

def preprocess_text(text):
    """
    Токенизация, очистка, удаление стоп-слов и лемматизация (если pymorphy2 доступен).
    Возвращает список лемм.
    """
    if not text:
        return []

    # Переводим в нижний регистр
    text = text.lower()

    # Убираем все символы кроме букв и пробелов
    text = re.sub(r'[^а-яё\s]', ' ', text)

    # Разбиваем на слова
    tokens = text.split()

    # Убираем стоп-слова
    tokens = [t for t in tokens if t not in russian_stopwords]

    # Лемматизация через pymorphy2, если доступно
    if PYMORPHY_AVAILABLE:
        try:
            lemmas = [morph.parse(t)[0].normal_form for t in tokens]
        except Exception:
            # Если что-то пошло не так — возвращаем исходные токены
            lemmas = tokens
    else:
        lemmas = tokens

    return lemmas
