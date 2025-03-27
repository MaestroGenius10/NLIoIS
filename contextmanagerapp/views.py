import re
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404
from .forms import WordEditForm, ArticleEditForm
from .models import Article, POSStats, WordAnalysis
import spacy
from collections import defaultdict
from PyPDF2 import PdfReader
from datetime import datetime
import string
from django.db import transaction


nlp = spacy.load("en_core_web_sm")
nlp.max_length = 2000000


def clean_text(text):
    text = text.replace('\r', '')  # Удаляем символы возврата каретки
    text = text.replace('\n', ' ')  # Заменяем символы новой строки на пробелы
    text = ' '.join(text.split())  # Удаляем лишние пробелы
    return text


def analyze_text(text, metadata_text=""):
    word_data = []
    pos_stats = defaultdict(int)
    intro_words = set()

    # Извлекаем вводную информацию из метаданных
    intro_end_index = metadata_text.find("AUTHORS:")
    if intro_end_index != -1:
        intro_text = metadata_text[:intro_end_index]
        intro_doc = nlp(intro_text)
        intro_words = {token.text.lower() for token in intro_doc}

    # Находим начало текста статьи (после метаданных)
    article_start_index = text.find("AUTHORS:")
    if article_start_index != -1:
        article_start_index = text.find("\n", article_start_index) + 1  # Переходим на следующую строку после "AUTHORS:"
        text = text[article_start_index:].strip()  # Обрезаем текст, оставляя только содержимое статьи

    # Очищаем текст от лишних символов
    text = clean_text(text)
    doc = nlp(text)  # Пересоздаем doc для обрезанного текста

    # Дополнительные символы пунктуации, которые нужно пропускать
    additional_punctuation = set('“”‘’"\'–…')

    # Регулярное выражение для чисел (включая числа с разделителями)
    number_pattern = re.compile(r'^[\d,:.\-]+$')

    for sentence in doc.sents:
        for token in sentence:
            word = token.text.lower()

            # Пропускаем пробелы, знаки пунктуации, дефисы, числа и слова из метаданных
            if (word in intro_words or
                word in string.punctuation or
                word.strip() == "" or
                "-" in word or
                number_pattern.match(word) or  # Пропускаем числа с разделителями
                any(char in additional_punctuation for char in word)):  # Пропускаем дополнительные символы пунктуации
                continue

            word_info = {
                "word": word,
                "lemma": token.lemma_,
                "pos": token.pos_,
                "morph": str(token.morph),
                "count": 1,
                "sentences": set(),  # Используем set для хранения уникальных предложений
                "additional_morphology": {}
            }

            # Обновляем статистику
            for entry in word_data:
                if entry["word"] == word:
                    entry["count"] += 1
                    entry["sentences"].add(sentence.text)  # Добавляем предложение в set
                    break
            else:
                word_info["sentences"].add(sentence.text)  # Добавляем предложение в set
                word_data.append(word_info)

            pos_stats[token.pos_] += 1

            # Дополнительные морфологические данные
            if token.pos_ == "NOUN":
                word_info["additional_morphology"]["number"] = "Sing" if "Sing" in token.morph.get("Number", "") else "Plur"
                word_info["additional_morphology"]["case"] = "Possessive" if "'s" in token.text else "Nominative"

            elif token.pos_ == "VERB":
                word_info["additional_morphology"]["tense"] = token.morph.get("Tense", ["Present"])[0]
                word_info["additional_morphology"]["person"] = token.morph.get("Person", ["3rd"])[0]
                word_info["additional_morphology"]["number"] = token.morph.get("Number", ["Sing"])[0]
                word_info["additional_morphology"]["mood"] = token.morph.get("Mood", ["Indicative"])[0]

            elif token.pos_ in ["ADJ", "ADV"]:
                word_info["additional_morphology"]["degree"] = token.morph.get("Degree", ["Positive"])[0]

    # Преобразуем set обратно в list для удобства
    for entry in word_data:
        entry["sentences"] = list(entry["sentences"])

    return word_data, pos_stats


def extract_articles(text):

    articles = text.split("================================================================================")
    article_list = []

    for article in articles:
        if not article.strip():
            continue  # Пропускаем пустые блоки

        # Разделяем метаданные и текст статьи
        metadata_end_index = article.find("AUTHORS:")
        if metadata_end_index == -1:
            continue  # Если нет метаданных, пропускаем

        metadata_end_index = article.find("\n", metadata_end_index) + 1  # Переходим на следующую строку после "AUTHORS:"
        metadata_text = article[:metadata_end_index].strip()
        article_text = article[metadata_end_index:].strip()

        article_list.append({
            "metadata_text": metadata_text,
            "article_text": article_text
        })

    return article_list


def extract_metadata_from_text(metadata_text):
    metadata = {}
    lines = metadata_text.strip().split("\n")

    for line in lines:
        if line.startswith("SPORT:"):
            metadata["sport"] = line.split("SPORT:")[1].strip()
        elif line.startswith("DATE:"):
            raw_date = line.split("DATE:")[1].strip()
            try:
                metadata["date"] = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                metadata["date"] = None
        elif line.startswith("TITLE:"):
            metadata["title"] = line.split("TITLE:")[1].strip()
        elif line.startswith("AUTHORS:"):
            metadata["authors"] = line.split("AUTHORS:")[1].strip()
        elif line.startswith("URL:"):
            metadata["url"] = line.split("URL:")[1].strip()

    return metadata


def read_file(file):
    file_extension = file.name.split('.')[-1].lower()
    if file_extension == 'txt':
        return file.read().decode('utf-8')
    elif file_extension == 'pdf':
        reader = PdfReader(file)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    else:
        raise ValueError("Unsupported file format")


def save_analysis(request):
    if request.method == 'POST':
        articles_data = request.session.get('articles_data', [])

        if not articles_data:
            return redirect('index')

        try:
            with transaction.atomic():
                for article_data in articles_data:
                    metadata = article_data['metadata']
                    article_text = article_data['article_text']
                    word_analysis = article_data['word_analysis']
                    pos_stats = article_data['pos_stats']

                    article = Article.objects.create(
                        title=metadata.get('title', ''),
                        author=metadata.get('authors', ''),
                        date=metadata.get('date', None),
                        sport=metadata.get('sport', ''),
                        content=article_text
                    )

                    POSStats.objects.bulk_create([
                        POSStats(article=article, pos_tag=pos, count=count) for pos, count in pos_stats.items()
                    ])

                    WordAnalysis.objects.bulk_create([
                        WordAnalysis(
                            article=article,
                            word=data["word"],
                            lemma=data["lemma"],
                            pos=data["pos"],
                            morphology=str(data["morph"]),
                            count=data["count"],
                            concordance="\n".join(data["sentences"])
                        ) for data in word_analysis
                    ])

            if 'articles_data' in request.session:
                del request.session['articles_data']

            return redirect('index')

        except Exception as e:
            print(f"Error saving analysis to database: {e}")
            return redirect('index')

    return redirect('index')




def view_dictionary(request):
    # Извлекаем все записи из WordAnalysis
    word_entries = WordAnalysis.objects.all()

    # Группируем слова по леммам
    dictionary = defaultdict(lambda: {
        "pos": set(),  # Уникальные части речи
        "count": 0,    # Общее количество вхождений
        "sentences": set(),  # Уникальные предложения
        "morphology": set()  # Уникальная морфология
    })

    for entry in word_entries:
        # Вычисляем лемму с помощью spacy
        doc = nlp(entry.word)
        lemma = doc[0].lemma_  # Лемма первого токена (слова)

        dictionary[lemma]["pos"].add(entry.pos)
        dictionary[lemma]["count"] += entry.count
        # Разделяем предложения по символу новой строки и добавляем в set
        sentences = entry.concordance.split('\n')
        dictionary[lemma]["sentences"].update(sentence.strip() for sentence in sentences if sentence.strip())
        dictionary[lemma]["morphology"].add(entry.morphology)

    # Преобразуем set в list для удобства отображения в шаблоне
    for lemma, data in dictionary.items():
        data["pos"] = list(data["pos"])
        data["sentences"] = list(data["sentences"])
        data["morphology"] = list(data["morphology"])
        dictionary[lemma]["id"] = entry.id

    # Сортируем словарь по леммам (алфавитный порядок)
    sorted_dictionary = sorted(dictionary.items(), key=lambda x: x[0])

    return render(request, 'dictionary.html', {'dictionary': sorted_dictionary})


def search_word(request):
    if request.method == 'GET':
        word = request.GET.get('word', '').strip()  # Получаем слово для поиска
        if not word:
            return render(request, 'search.html', {'error': 'Введите слово для поиска.'})

        # Ищем статьи, содержащие слово
        articles = Article.objects.filter(content__icontains=word)  # Поиск по частичному совпадению в тексте статьи

        if not articles:
            return render(request, 'search.html', {'error': f'Статьи, содержащие слово "{word}", не найдены.'})

        # Собираем результаты
        results = []
        for article in articles:
            # Извлекаем метаданные статьи
            metadata = {
                'title': article.title,
                'author': article.author,
                'date': article.date,
                'sport': article.sport,
            }

            # Ищем точное совпадение слова в WordAnalysis
            word_analysis = WordAnalysis.objects.filter(
                article=article,
                word__iexact=word  # Точное совпадение слова (без учёта регистра)
            )

            if not word_analysis:
                continue  # Пропускаем, если слово не найдено в анализе

            # Группируем данные по леммам
            dictionary = defaultdict(lambda: {
                "pos": set(),  # Уникальные части речи
                "count": 0,    # Общее количество вхождений
                "sentences": set(),  # Уникальные предложения
                "morphology": set()  # Уникальная морфология
            })

            for entry in word_analysis:
                # Вычисляем лемму с помощью spacy
                doc = nlp(entry.word)
                lemma = doc[0].lemma_  # Лемма первого токена (слова)

                dictionary[lemma]["pos"].add(entry.pos)
                dictionary[lemma]["count"] += entry.count
                # Разделяем предложения по символу новой строки и добавляем в set
                sentences = entry.concordance.split('\n')
                dictionary[lemma]["sentences"].update(sentence.strip() for sentence in sentences if sentence.strip())
                dictionary[lemma]["morphology"].add(entry.morphology)  # Добавляем морфологию
                dictionary[lemma]["id"] = entry.id
            # Преобразуем set в list для удобства отображения в шаблоне
            for lemma, data in dictionary.items():
                data["pos"] = list(data["pos"])
                data["sentences"] = list(data["sentences"])
                data["morphology"] = list(data["morphology"])

            # Сортируем словарь по леммам (алфавитный порядок)
            sorted_dictionary = sorted(dictionary.items(), key=lambda x: x[0])

            results.append({
                'metadata': metadata,
                'dictionary': sorted_dictionary
            })

        if not results:
            return render(request, 'search.html', {'error': f'Слово "{word}" не найдено в статьях.'})

        return render(request, 'search.html', {'word_results': results, 'word': word})

    return render(request, 'search.html')


def search_phrase(request):
    if request.method == 'GET':
        phrase = request.GET.get('phrase', '').strip()  # Получаем фразу для поиска
        if not phrase:
            return render(request, 'search.html', {'error': 'Введите фразу для поиска.'})

        # Ищем статьи, содержащие точное совпадение фразы
        articles = Article.objects.filter(content__icontains=phrase)

        if not articles:
            return render(request, 'search.html', {'error': f'Статьи, содержащие фразу "{phrase}", не найдены.'})

        # Собираем результаты
        results = []
        for article in articles:
            # Извлекаем метаданные статьи
            metadata = {
                'title': article.title,
                'author': article.author,
                'date': article.date,
                'sport': article.sport,
            }

            # Ищем конкорданс (предложения, содержащие фразу)
            sentences = []
            for sentence in article.content.split('.'):  # Разделяем текст на предложения
                if phrase.lower() in sentence.lower():
                    sentences.append(sentence.strip())

            if not sentences:
                continue  # Пропускаем, если фраза не найдена в предложениях

            results.append({
                'metadata': metadata,
                'concordance': sentences  # Конкорданс (предложения с фразой)
            })

        if not results:
            return render(request, 'search.html', {'error': f'Фраза "{phrase}" не найдена в статьях.'})

        return render(request, 'search.html', {'phrase_results': results, 'phrase': phrase})

    return render(request, 'search.html')


def edit_word(request, word_id):
    # Получаем слово для редактирования
    word = get_object_or_404(WordAnalysis, id=word_id)

    if request.method == 'POST':
        # Если данные отправлены, обрабатываем форму
        form = WordEditForm(request.POST, instance=word)
        if form.is_valid():
            form.save()
            return redirect('view_dictionary')
    else:
        # Если GET-запрос, отображаем форму с текущими данными
        form = WordEditForm(instance=word)

    return render(request, 'edit_word.html', {'form': form, 'word': word})


def update_word(request, word_id):
    # Получаем слово для обновления
    word = get_object_or_404(WordAnalysis, id=word_id)

    if request.method == 'POST':
        # Обновляем данные слова
        word.word = request.POST.get('word')
        word.lemma = request.POST.get('lemma')
        word.pos = request.POST.get('pos')
        word.morphology = request.POST.get('morphology')
        word.count = request.POST.get('count')
        word.concordance = request.POST.get('concordance')
        word.save()
        return redirect('view_dictionary')

    return redirect('edit_word', word_id=word_id)


def view_articles(request):
    # Получаем все статьи
    articles = Article.objects.all()

    # Собираем статистику по частям речи для каждой статьи
    articles_stats = []
    for article in articles:
        pos_stats = POSStats.objects.filter(article=article)
        stats = {stat.pos_tag: stat.count for stat in pos_stats}
        articles_stats.append({
            'article': article,
            'pos_stats': stats
        })

    # Собираем общую статистику по всему корпусу
    total_stats = {}
    for stat in POSStats.objects.all():
        if stat.pos_tag in total_stats:
            total_stats[stat.pos_tag] += stat.count
        else:
            total_stats[stat.pos_tag] = stat.count

    # Передаем данные в шаблон
    return render(request, 'articles.html', {
        'articles_stats': articles_stats,
        'total_stats': total_stats
    })


def view_article_text(request, article_id):
    # Получаем статью по её ID
    article = get_object_or_404(Article, id=article_id)

    # Отображаем шаблон с текстом статьи
    return render(request, 'article_text.html', {
        'article': article
    })


def edit_article(request, article_id):
    # Получаем статью по её ID
    article = get_object_or_404(Article, id=article_id)

    if request.method == 'POST':
        # Если данные отправлены, обрабатываем форму
        form = ArticleEditForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return redirect('view_article_text', article_id=article.id)  # Перенаправляем на страницу статьи
    else:
        # Если GET-запрос, отображаем форму с текущими данными
        form = ArticleEditForm(instance=article)

    return render(request, 'edit_article.html', {'form': form, 'article': article})