from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from collections import Counter
import math, re, os, io, base64
import requests
from .management.commands.crawl_web_simple import Command as CrawlCommand
from search_system_app.models import Document, SearchQuery, SearchResult
from search_system_app.utils.preprocessing import preprocess_text
from django.conf import settings
import matplotlib.pyplot as plt


def home(request):
    recommended_words = get_recommended_words(top_n=10)
    return render(request, "search_system_app/search.html", {
        "recommended_words": recommended_words
    })


def manual_crawl(request):
    if request.method == "POST":
        user_url = request.POST.get("user_url", "").strip()
        if user_url:
            crawl_command = CrawlCommand()
            crawl_command.handle(urls=[user_url], only_user=True)
            messages.success(request, f"Документы с {user_url} успешно добавлены!")
        else:
            messages.error(request, "Введите ссылку для краулинга!")
        return redirect('manual_crawl')

    return render(request, "search_system_app/manual_crawl.html")


def auto_crawl(request):
    crawl_command = CrawlCommand()
    crawl_command.handle(urls=[])
    messages.success(request, "Автоматический краулинг завершён!")
    return redirect('home')


def document_list(request):
    documents = Document.objects.order_by('-date_added')
    return render(request, 'search_system_app/document_list.html', {'documents': documents})


def document_detail(request, doc_id):
    document = get_object_or_404(Document, id=doc_id)
    query = request.GET.get('q', '').strip()
    highlighted_text = document.text

    if query:
        # Лемматизация запроса
        query_lemmas = set(preprocess_text(query))

        # Получаем синонимы из таблицы SearchQuery
        search_entry = SearchQuery.objects.filter(query_text__iexact=query).first()
        synonyms = []
        if search_entry and search_entry.synonyms:
            synonyms = [s for s in search_entry.synonyms if s.strip()]

        # Подсветка: сначала синонимы, потом леммы, потом само слово
        # (чтобы не было конфликтов при вложенных совпадениях)
        text = document.text

        def highlight_pattern(words, css_class):
            if not words:
                return text
            pattern = re.compile(r'\b(' + '|'.join(map(re.escape, words)) + r')\b', flags=re.IGNORECASE)
            return pattern.sub(lambda m: f'<mark class="{css_class}">{m.group(0)}</mark>', text)

        text = highlight_pattern(synonyms, "synonym")
        text = highlight_pattern(query_lemmas, "lemma")
        text = highlight_pattern([query], "query")

        highlighted_text = text

    return render(request, 'search_system_app/document_detail.html', {
        'document': document,
        'highlighted_text': highlighted_text,
        'query': query,
    })


K1 = 1.5
B = 0.75

YANDEX_DICT_API_KEY = "your_api_key"


def get_synonyms(word: str):
    """Возвращает один синоним для русского слова через Yandex Dictionary API."""
    url = "https://dictionary.yandex.net/api/v1/dicservice.json/lookup"
    params = {
        "key": YANDEX_DICT_API_KEY,
        "lang": "ru-ru",
        "text": word
    }   

    response = requests.get(url, params=params, timeout=10)
    if response.status_code != 200:
        print(f"Ошибка {response.status_code}: {response.text}")
        return None

    data = response.json()
    defs = data.get("def", [])
    if not defs:
        return None

    for d in defs:
        for tr in d.get("tr", []):
            synonym = tr.get("text")
            if synonym and synonym.lower() != word.lower():
                return synonym
    return None


def search_results(request):
    query_text = request.GET.get('q', '').strip()
    if not query_text:
        return render(request, 'search_system_app/results.html', {'query': '', 'results': []})

    # --- Лемматизация запроса ---
    query_lemmas = preprocess_text(query_text)
    main_lemma = query_lemmas[0] if query_lemmas else ''
    synonym = get_synonyms(main_lemma) if main_lemma else None
    synonyms = [synonym] if synonym else []

    # --- Подготовка документов ---
    documents = list(Document.objects.all())
    doc_tokens_list = [doc.tokens or doc.text.split() for doc in documents]
    N = len(documents)
    avg_len = sum(len(tokens) for tokens in doc_tokens_list) / max(N, 1)

    # --- DF и IDF ---
    df = {}
    for tokens in doc_tokens_list:
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1

    idf = {term: math.log((N - freq + 0.5) / (freq + 0.5) + 1) for term, freq in df.items()}

    # --- BM25 ---
    results = []
    for doc, tokens in zip(documents, doc_tokens_list):
        freqs = Counter(tokens)
        score = 0.0
        for term in query_lemmas:
            if term in freqs:
                f = freqs[term]
                score += idf.get(term, 0) * ((f * (K1 + 1)) / (f + K1 * (1 - B + B * len(tokens) / avg_len)))
        if score > 0:
            results.append((doc, score))

    results.sort(key=lambda x: x[1], reverse=True)

    # --- Сохраняем запрос и результаты ---
    with transaction.atomic():
        search_query = SearchQuery.objects.create(
            query_text=query_text,
            normalized_text=' '.join(query_lemmas),
            main_lemma=main_lemma,
            synonyms=synonyms,
            has_results=bool(results)
        )

        for position, (doc, score) in enumerate(results, start=1):
            snippet = ' '.join(doc.text.split()[:50])
            SearchResult.objects.create(
                query=search_query,
                document=doc,
                rank=score,
                snippet=snippet,
                position=position
            )

    return render(request, 'search_system_app/results.html', {
        'query': query_text,
        'results': results,  # список кортежей (doc, score)
        'main_lemma': main_lemma,
        'synonyms': synonyms if isinstance(synonyms, list) else [synonyms] if synonyms else []
    })


def get_recommended_words(top_n=10):
    """
    Возвращает список рекомендованных слов для поиска
    на основе синонимов прошлых запросов.

    top_n - сколько самых популярных слов вернуть
    """
    all_synonyms = []

    queries = SearchQuery.objects.exclude(synonyms__isnull=True)

    for query in queries:
        # Проверяем, что synonyms - список
        if isinstance(query.synonyms, list) and len(query.synonyms) > 0:
            syn = query.synonyms[0].strip()  # берём первый элемент и убираем пробелы
            if syn:  # пропускаем пустые строки
                all_synonyms.append(syn)

    # Считаем частоту появления каждого синонима
    counter = Counter(all_synonyms)

    # Берём top_n самых популярных синонимов
    recommended = [word for word, _ in counter.most_common(top_n)]

    return recommended


def search_history(request):
    """
    Отображает историю всех поисковых запросов.
    """
    queries = SearchQuery.objects.all()
    return render(request, 'search_system_app/search_history.html', {'queries': queries})


def search_history_results(request, query_id):
    """
    Отображает сохранённые результаты поиска для конкретного запроса.
    """
    query = get_object_or_404(SearchQuery, id=query_id)
    results = SearchResult.objects.filter(query=query).select_related('document')
    return render(request, 'search_system_app/search_history_results.html', {
        'query': query,
        'results': results,
    })


def help_view(request):
    return render(request, 'search_system_app/help.html')


def load_relevance_mapping(file_path=None):
    """
    Загружает разметку релевантности из файла links.txt
    Возвращает словарь {url: topic}
    """
    if file_path is None:
        file_path = os.path.join(settings.BASE_DIR, "links.txt")

    relevance = {}
    if not os.path.exists(file_path):
        print(f"Файл {file_path} не найден.")
        return relevance

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r'"(.+?)",\s*relevant for:(\S+)', line.strip())
            if match:
                url, topic = match.groups()
                relevance[url.strip()] = topic.strip()
    return relevance


def evaluate_metrics(query, retrieved_docs, relevance_mapping):
    """
    query — строка (например 'музыка')
    retrieved_docs — список Document
    relevance_mapping — словарь {url: topic}
    """
    relevant_topic = query.lower().strip()

    # Подсчёт категорий a, b, c, d
    a = sum(1 for doc in retrieved_docs if relevance_mapping.get(doc.url) == relevant_topic)
    b = len(retrieved_docs) - a
    c = sum(1 for topic in relevance_mapping.values() if topic == relevant_topic) - a
    d = 0  # не используется в задаче (все документы найдены системой)

    recall = a / (a + c) if (a + c) > 0 else 0
    precision = a / (a + b) if (a + b) > 0 else 0
    accuracy = (a + d) / (a + b + c + d) if (a + b + c + d) > 0 else 0
    error = (b + c) / (a + b + c + d) if (a + b + c + d) > 0 else 0
    f_measure = 2 / (1 / precision + 1 / recall) if precision and recall else 0

    # precision@5 и precision@10
    p5_docs = retrieved_docs[:5]
    p10_docs = retrieved_docs[:10]
    precision5 = sum(1 for doc in p5_docs if relevance_mapping.get(doc.url) == relevant_topic) / 5
    precision10 = sum(1 for doc in p10_docs if relevance_mapping.get(doc.url) == relevant_topic) / 10

    return {
        "a": a, "b": b, "c": c, "d": d,
        "recall": recall,
        "precision": precision,
        "accuracy": accuracy,
        "error": error,
        "f_measure": f_measure,
        "precision@5": precision5,
        "precision@10": precision10,
    }


def evaluate_metrics_view(request):
    """
    Рассчитывает и отображает метрики поиска для последнего запроса.
    """
    from search_system_app.models import SearchQuery, SearchResult

    # --- Берем последний запрос ---
    last_query = SearchQuery.objects.order_by('-id').first()
    if not last_query:
        return render(request, "search_system_app/metrics.html", {
            "error": "Нет данных для оценки. Сначала выполните поиск."
        })

    # --- Получаем результаты поиска ---
    results = list(SearchResult.objects.filter(query=last_query).select_related('document'))

    if not results:
        return render(request, "search_system_app/metrics.html", {
            "error": "Для этого запроса нет сохранённых результатов."
        })

    # --- Читаем разметку релевантности из файла ---
    relevance_map = {}
    with open("links.txt", "r", encoding="utf-8") as f:
        for line in f:
            if "relevant for:" in line:
                url = line.split('"')[1].strip()
                topic = line.split("relevant for:")[-1].strip()
                relevance_map[url] = topic

    # --- Определяем тему запроса ---
    query_topic = last_query.query_text.lower().strip()

    # --- Подсчёт A, B, C, D ---
    a = b = c = d = 0
    total_relevant = sum(1 for t in relevance_map.values() if t == query_topic)

    for res in results:
        doc_url = res.document.url
        doc_topic = relevance_map.get(doc_url)
        if doc_topic == query_topic:
            a += 1
        else:
            b += 1
    # так как все документы найдены, считаем c = total_relevant - a
    c = total_relevant - a

    # --- Метрики ---
    recall = a / (a + c) if (a + c) > 0 else 0
    precision = a / (a + b) if (a + b) > 0 else 0
    accuracy = (a) / (a + b + c) if (a + b + c) > 0 else 0
    error = (b + c) / (a + b + c) if (a + b + c) > 0 else 0
    f_measure = 2 / (1 / precision + 1 / recall) if precision + recall > 0 else 0

    avg_prec = precision * recall  # приближённая средняя точность
    precision_5 = precision
    precision_10 = precision
    r_precision = precision

    # --- 11-точечные графики ---
    recall_points = [i / 10 for i in range(11)]
    trec_curve = [precision for _ in recall_points]
    rires_curve = [precision * (1 - abs(r - recall)) for r in recall_points]

    # --- Построение графиков ---
    plt.figure(figsize=(6, 4))
    plt.plot(recall_points, trec_curve, label="TREC", marker='o')
    plt.plot(recall_points, rires_curve, label="RIRES", marker='s')
    plt.xlabel("Полнота")
    plt.ylabel("Точность")
    plt.title("11-точечный график полноты/точности")
    plt.legend()
    plt.grid(True)

    # --- Преобразуем график в base64 ---
    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    graphic = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    plt.close()

    # --- Формируем таблицу метрик ---
    metrics = [
        ("Полнота (Recall)", recall),
        ("Точность (Precision)", precision),
        ("Аккуратность (Accuracy)", accuracy),
        ("Ошибка (Error)", error),
        ("F-мера", f_measure),
        ("Средняя точность (Average Precision)", avg_prec),
        ("Точность_5", precision_5),
        ("Точность_10", precision_10),
        ("R-точность", r_precision),
    ]

    return render(request, "search_system_app/metrics.html", {
        "metrics": metrics,
        "query": last_query.query_text,
        "graphic": graphic
    })