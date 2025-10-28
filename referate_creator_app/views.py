from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest
from .models import Document, Summary, Sentence, Keyword
from .utils.file_reader import extract_text_from_file
import os
from .utils.ollama_client import generate_keywords_via_ollama
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import re
from django.urls import reverse
from .utils.summarizer import RUSSIAN_STOPWORDS
from django.template.loader import render_to_string
from django.http import HttpResponseBadRequest, HttpResponse


def index(request):
    """Главная страница с формой загрузки документов."""
    return render(request, "referate_creator_app/index.html")


def documents_list(request):
    """Страница со списком загруженных документов."""
    documents = Document.objects.all().order_by("-upload_date")
    return render(request, "referate_creator_app/documents_list.html", {"documents": documents})


def upload_document(request):
    """Обработка загрузки одного или нескольких файлов."""
    if request.method != "POST":
        return HttpResponseBadRequest("Некорректный метод запроса.")

    files = request.FILES.getlist("source_file")
    if not files:
        return HttpResponseBadRequest("Файлы не выбраны.")

    valid_exts = [".pdf", ".txt", ".doc", ".docx"]

    for f in files:
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in valid_exts:
            return HttpResponseBadRequest(f"Неподдерживаемый формат файла: {f.name}")

        document = Document.objects.create(
            title=os.path.splitext(f.name)[0],
            source_file=f,
        )

        try:
            text = extract_text_from_file(document.source_file.path)
            document.text_content = text
            document.processed = True
            document.save()
        except Exception as e:
            print(f"[Ошибка при извлечении текста]: {e}")

    return redirect("documents_list")


def document_detail(request, doc_id):
    """Просмотр полного текста документа."""
    document = get_object_or_404(Document, id=doc_id)
    return render(request, "referate_creator_app/document_detail.html", {"document": document})


def select_documents(request):
    """
    Страница выбора документов для реферирования.
    """
    documents = Document.objects.all().order_by("-upload_date")

    if request.method == "POST":
        selected_ids = request.POST.getlist("documents")
        if not selected_ids:
            return redirect("select_documents")

        request.session['selected_doc_ids'] = [int(id) for id in selected_ids]

        # ИЗМЕНЕНИЕ 2: Перенаправляем на чистый URL без параметров
        return redirect("referencing_results")

    return render(request, "referate_creator_app/select_documents.html", {"documents": documents})


def referencing_results(request):
    """
    Страница с результатами реферирования и сохранением в БД.
    """
    # ИЗМЕНЕНИЕ 3: Получаем ID из сессии, а не из request.GET
    id_list = request.session.get('selected_doc_ids', [])

    if not id_list:
        # Если в сессии по какой-то причине нет ID, отправляем на страницу выбора
        return redirect("select_documents")

    documents = Document.objects.filter(id__in=id_list)
    results = []

    for doc in documents:
        text = doc.text_content

        # ---------- 1. Классический реферат через TF-IDF ----------
        sentences_data, summary_sentences = generate_classic_summary(text, top_n=10)

        # Сохраняем предложения и отмечаем те, что вошли в реферат
        Sentence.objects.filter(document=doc).delete()
        for idx, (sent_text, weight) in enumerate(sentences_data):
            Sentence.objects.create(
                document=doc,
                text=sent_text,
                weight=weight,
                order_in_text=idx,
                selected_for_summary=(sent_text in summary_sentences)
            )

        # Создаем специальный список для отображения, отсортированный по весу
        summary_with_weights = []
        for sentence, weight in sentences_data:
            if sentence in summary_sentences:
                summary_with_weights.append({'text': sentence, 'weight': weight})

        sorted_summary_for_display = sorted(summary_with_weights, key=lambda x: x['weight'], reverse=True)
        classic_summary_for_db = "\n".join(summary_sentences)

        # ---------- 2. Реферат ключевых слов через Ollama ----------
        keywords_summary = generate_keywords_via_ollama(text)

        # Улучшаем форматирование ключевых слов для вывода
        formatted_keywords = []
        for line in keywords_summary.splitlines():
            clean_line = line.strip()
            if clean_line.startswith('*'):
                formatted_keywords.append(f"• {clean_line.lstrip('* ').strip()}")
            elif clean_line.startswith('+'):
                formatted_keywords.append(f"  ◦ {clean_line.lstrip('+ ').strip()}")
            else:
                formatted_keywords.append(clean_line)

        keywords_for_display = "\n".join(formatted_keywords)

        # ---------- Сохраняем готовые рефераты ----------
        Summary.objects.update_or_create(
            document=doc,
            summary_type="classic",
            defaults={"content": classic_summary_for_db, "generation_method": "tfidf"}
        )
        Summary.objects.update_or_create(
            document=doc,
            summary_type="keywords",
            defaults={"content": keywords_summary, "generation_method": "ollama"}
        )

        results.append({
            "document": doc,
            "classic_summary_sorted": sorted_summary_for_display,
            "keywords_formatted": keywords_for_display,
        })

    # ИЗМЕНЕНИЕ 4: Контекст теперь не содержит ids_str
    return render(
        request,
        "referate_creator_app/referencing_results.html",
        {"results": results}
    )


def generate_classic_summary(text: str, top_n: int = 10):
    """
    Классическое реферирование методом Sentence Extraction + TF-IDF.
    Возвращает:
      - список всех предложений с их весами [(sentence, weight), ...]
      - список предложений, которые вошли в реферат
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if not sentences or not any(s.strip() for s in sentences):
        return [], []

    if len(sentences) <= 3:
        sentences_data = [(s, 1.0) for s in sentences]
        return sentences_data, sentences

    vectorizer = TfidfVectorizer(
        stop_words=list(RUSSIAN_STOPWORDS),
        lowercase=True,
        # ИЗМЕНЕНИЕ: Добавлены латинские буквы a-zA-Z
        token_pattern=r"[a-zA-Zа-яА-ЯёЁ]+"
    )

    try:
        X = vectorizer.fit_transform(sentences)
        sentence_scores = np.asarray(X.sum(axis=1)).ravel()
        sentences_data = list(zip(sentences, sentence_scores))
        top_indices = sorted(np.argsort(sentence_scores)[-top_n:])
        summary_sentences = [sentences[i] for i in top_indices]

    except ValueError:
        print(
            f"[Warning] ValueError: empty vocabulary. The document likely contains only stop words or unsupported characters.")
        summary_sentences = sentences[:top_n]
        sentences_data = [(s, 0.0) for s in sentences]

    return sentences_data, summary_sentences


# views.py

# ... (все импорты в начале файла остаются без изменений) ...

def download_report(request):
    """
    Формирует HTML-файл с полным отчетом и отдает его для скачивания.
    """
    id_list = request.session.get('selected_doc_ids', [])

    if not id_list:
        return redirect("select_documents")

    documents = Document.objects.filter(id__in=id_list).prefetch_related('summaries')

    # ИЗМЕНЕНИЕ: Подготавливаем данные прямо здесь, в представлении
    for doc in documents:
        # Устанавливаем значения по умолчанию
        doc.classic_summary_content = "Реферат не был сгенерирован."
        doc.keywords_summary_content = "Реферат не был сгенерирован."
        # Ищем нужные рефераты в связанной коллекции
        for summary in doc.summaries.all():
            if summary.summary_type == 'classic':
                doc.classic_summary_content = summary.content
            elif summary.summary_type == 'keywords':
                doc.keywords_summary_content = summary.content

    context = {
        'documents': documents
    }

    html_content = render_to_string(
        'referate_creator_app/download_report.html',
        context
    )

    response = HttpResponse(html_content, content_type='text/html; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="report.html"'

    return response


def history_list(request):
    """
    Отображает страницу с историей реферирования:
    для каждого документа показывается самый свежий результат.
    """
    # 1. Находим все документы, у которых есть хотя бы один реферат.
    docs_with_history = Document.objects.filter(summaries__isnull=False).distinct()

    history_results = []
    for doc in docs_with_history:
        # 2. Для каждого документа находим самый последний по дате классический реферат.
        latest_classic = doc.summaries.filter(
            summary_type='classic'
        ).order_by('-created_at').first()

        # 3. Находим самый последний реферат ключевых слов.
        latest_keywords_summary = doc.summaries.filter(
            summary_type='keywords'
        ).order_by('-created_at').first()

        # Если по какой-то причине одного из рефератов нет, мы пропускаем этот документ
        if not latest_classic or not latest_keywords_summary:
            continue

        # 4. Форматируем ключевые слова для красивого вывода, как на странице результатов
        formatted_keywords = []
        for line in latest_keywords_summary.content.splitlines():
            clean_line = line.strip()
            if clean_line.startswith('*'):
                formatted_keywords.append(f"• {clean_line.lstrip('* ').strip()}")
            elif clean_line.startswith('+'):
                formatted_keywords.append(f"  ◦ {clean_line.lstrip('+ ').strip()}")
            else:
                formatted_keywords.append(clean_line)

        keywords_for_display = "\n".join(formatted_keywords)

        # 5. Собираем все данные в один словарь
        history_results.append({
            'document': doc,
            'classic_summary': latest_classic,
            'keywords_formatted': keywords_for_display,
        })

    # 6. Сортируем итоговый список так, чтобы самые свежие результаты были вверху
    history_results.sort(key=lambda x: x['classic_summary'].created_at, reverse=True)

    return render(
        request,
        'referate_creator_app/history_list.html',
        {'history_results': history_results}
    )


def help_page(request):
    """
    Отображает статичную страницу справки по системе.
    """
    return render(request, 'referate_creator_app/help_page.html')