<<<<<<< HEAD
import json
=======
# translator_app/views.py

import json
import requests
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
import spacy
from collections import Counter
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
<<<<<<< HEAD
from .models import (
    Document, TranslationPair, WordAnalysisEn, WordAnalysisRu,
    LemmaEn, LemmaRu, DictionaryPair
)
from django.conf import settings
import requests
from django.contrib import messages
from django.http import HttpResponse
=======
from .models import Document, TranslationPair, WordAnalysisEn, WordAnalysisRu, WordDictionary

# --- Загрузка моделей spaCy ---
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
try:
    nlp_en = spacy.load("en_core_web_sm")
    nlp_ru = spacy.load("ru_core_news_sm")
    print("✅ SpaCy models loaded successfully.")
except OSError:
    print("❌ SpaCy models not found. Please run the download commands.")
    nlp_en, nlp_ru = None, None
<<<<<<< HEAD

# --- Словарь для расшифровки тегов частей речи ---
POS_TAGS_DESC = {
    'NOUN': 'Существительное', 'VERB': 'Глагол', 'ADJ': 'Прилагательное', 'ADV': 'Наречие',
    'PROPN': 'Имя собственное', 'NUM': 'Числительное', 'PRON': 'Местоимение', 'ADP': 'Предлог',
    'AUX': 'Вспомогательный глагол', 'CCONJ': 'Сочинительный союз', 'SCONJ': 'Подчинительный союз',
=======
# -----------------------------

# Словарь для расшифровки тегов частей речи для вывода в шаблонах
POS_TAGS_DESC = {
    'NOUN': 'Существительное', 'VERB': 'Глагол', 'ADJ': 'Прилагательное',
    'ADV': 'Наречие', 'PROPN': 'Имя собственное', 'NUM': 'Числительное',
    'PRON': 'Местоимение', 'ADP': 'Предлог', 'AUX': 'Вспомогательный глагол',
    'CCONJ': 'Сочинительный союз', 'SCONJ': 'Подчинительный союз',
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
    'DET': 'Определитель (артикль)', 'INTJ': 'Междометие', 'PART': 'Частица',
    'PUNCT': 'Пунктуация', 'SYM': 'Символ', 'X': 'Другое', 'SPACE': 'Пробел'
}


# ==========================================================
# 1. ОСНОВНЫЕ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================================

<<<<<<< HEAD
import json
import requests
from django.conf import settings

def translate_text_smart(text_to_translate):
    """
    УЛУЧШЕННАЯ ВЕРСИЯ 2.0: Обрабатывает нестандартные ответы от API,
    когда результат приходит в поле 'reasoning', а не 'content',
    а также очищает строку от "мусора" после JSON-объекта.
    """
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        print("❌ OPENROUTER_API_KEY не найден в настройках.")
        return None

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Translator App"
    }
    model_name ="deepseek/deepseek-chat-v3.1:free"
    prompt_content = (
        "You are an expert linguistic analysis tool. Your task is to process an English text and provide two things: a flawless Russian translation and a precise word alignment map. "
        "You MUST respond with a single, raw JSON object and nothing else. The JSON object must have this exact structure:\n"
        "{\n"
        '  "translation": "The full, high-quality Russian translation of the text.",\n'
        '  "word_map": [\n'
        '    {"source": "english_lemma", "target": "russian_lemma"},\n'
        '    {"source": "another_lemma", "target": "another_russian_lemma"}\n'
        '  ]\n'
        "}\n"
        "Follow these critical rules for the 'word_map':\n"
        "1.  **Use Lemmas**: Always provide the base form (lemma) of the words in lowercase (e.g., for 'cars' use 'car', for 'went' use 'go').\n"
        "2.  **Meaningful Words Only**: Only include nouns, verbs, adjectives, and adverbs in the map. Exclude prepositions, articles, conjunctions, etc.\n"
        "3.  **Accuracy is Key**: The source and target lemmas must be accurate semantic equivalents in the context of the text.\n"
        "4.  **No Extra Text**: Your entire output must be only the JSON object, starting with `{` and ending with `}`."
    )
    data = {
        "model": model_name,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": prompt_content},
            {"role": "user", "content": text_to_translate}
        ]
    }

    response_data = None
    json_string = None
    try:
        response = requests.post(url, headers=headers, json=data, timeout=180)
        response.raise_for_status()
        response_data = response.json()

        if not response_data.get('choices'):
            print("❌ Ответ от API не содержит ключ 'choices'. Полный ответ:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            return None

        message_block = response_data['choices'][0]['message']

        # --- НАЧАЛО: ИСПРАВЛЕННАЯ ЛОГИКА ---
        # 1. Проверяем стандартное поле 'content'.
        json_string = message_block.get('content')

        # 2. Если оно пустое, проверяем нестандартное поле 'reasoning'.
        if not json_string or not json_string.strip():
            print("ℹ️ Поле 'content' пустое. Проверяем нестандартное поле 'reasoning'...")
            json_string = message_block.get('reasoning')

        # 3. Если и там пусто, то ответа нет.
        if not json_string or not json_string.strip():
            print("❌ API вернул пустой ответ и в 'content', и в 'reasoning'.")
            print("Полный ответ от API для диагностики:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            return None

        # 4. Очищаем строку от возможного "мусора" после JSON
        last_brace_index = json_string.rfind('}')
        if last_brace_index != -1:
            json_string = json_string[:last_brace_index + 1]
        else:
            print(f"❌ Не найдена закрывающая скобка '}}' в ответе от API: {json_string}")
            return None
        # --- КОНЕЦ: ИСПРАВЛЕННАЯ ЛОГИКА ---

        parsed_json = json.loads(json_string)
        if 'translation' in parsed_json and 'word_map' in parsed_json:
            return parsed_json
        else:
            print("❌ Разобранный JSON не содержит ключей 'translation' или 'word_map'.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Произошла ошибка при вызове OpenRouter API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"❌ Тело ответа: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Не удалось разобрать JSON от OpenRouter API. Ошибка: {e}")
        if json_string:
            print("Строка, которую не удалось разобрать:", json_string)
        return None
    except (KeyError, IndexError) as e:
        print(f"❌ Неверная структура ответа от OpenRouter API. Ошибка ключа или индекса: {e}")
        if response_data:
            print("Полный ответ, который вызвал ошибку:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
        return None


def save_dictionary_and_pos(word_map, source_text, target_text):
    """
    УЛУЧШЕННАЯ ВЕРСИЯ: Принимает карту слов от API, а также полные тексты.
    Использует spaCy для определения частей речи и сохраняет их вместе с леммами
    в глобальный словарь.
    """
    if not isinstance(word_map, list) or not nlp_en or not nlp_ru:
        return

    spacy_source_doc = nlp_en(source_text)
    spacy_pos_map_en = {token.lemma_.lower(): token.pos_ for token in spacy_source_doc}

    spacy_target_doc = nlp_ru(target_text)
    spacy_pos_map_ru = {token.lemma_.lower(): token.pos_ for token in spacy_target_doc}

    for pair in word_map:
        source_lemma_str = pair.get('source', '').lower().strip()
        target_lemma_str = pair.get('target', '').lower().strip()

        if not source_lemma_str or not target_lemma_str:
            continue

        source_pos = spacy_pos_map_en.get(source_lemma_str, '')
        target_pos = spacy_pos_map_ru.get(target_lemma_str, '')

        source_lemma_obj, created_en = LemmaEn.objects.get_or_create(
            lemma=source_lemma_str,
            defaults={'pos': source_pos}
        )
        if not created_en and not source_lemma_obj.pos and source_pos:
            source_lemma_obj.pos = source_pos
            source_lemma_obj.save()

        target_lemma_obj, created_ru = LemmaRu.objects.get_or_create(
            lemma=target_lemma_str,
            defaults={'pos': target_pos}
        )
        if not created_ru and not target_lemma_obj.pos and target_pos:
            target_lemma_obj.pos = target_pos
            target_lemma_obj.save()

        dict_pair, created_pair = DictionaryPair.objects.get_or_create(
            source_lemma=source_lemma_obj,
            target_lemma=target_lemma_obj
        )
        if not created_pair:
            dict_pair.translation_count += 1
            dict_pair.save()


def process_and_save_word_pairs(source_doc, target_doc):
    """
    ИСПРАВЛЕННАЯ ВЕРСИЯ: Эта функция теперь корректно собирает статистику,
    правильно подсчитывая частоту каждого слова в документе.
    """
    if not nlp_en or not nlp_ru:
        print("SpaCy models not loaded. Skipping word analysis.")
        return

    POS_TO_IGNORE = ['ADP', 'CCONJ', 'DET', 'PUNCT', 'SPACE', 'PART', 'SCONJ', 'AUX', 'SYM', 'X']
=======
def translate_text_smart(text_to_translate):
    """
    ФИНАЛЬНАЯ ВЕРСИЯ: Использует максимально четкий и строгий экспертный промпт,
    доверяя модели перевод терминов, но задавая жесткие рамки по стилю и полноте.
    """

    # Шаг 1: Формируем финальный, недвусмысленный промпт.
    system_instruction = (
        "You are an expert translator with a Ph.D. in medical science, specializing in translating English oncology research papers for a prestigious Russian scientific journal. "
        "Your task is to translate the provided English text into Russian with absolute precision, maintaining a formal scientific tone."
    )

    rules = [
        "1. Translate ALL content from English to Russian. You must not leave any English words, phrases, or technical terms untranslated. Find the correct Russian scientific equivalent for every term.",
        "2. Use formal, scientific Russian terminology appropriate for oncology. Maintain a professional, academic tone throughout the text.",
        "3. Ensure the sentence structure is natural and grammatically flawless for the Russian language. Rephrase complex English sentences to be clear and concise in Russian.",
        "4. If you encounter a potential typo or grammatical error in the source English text (e.g., 'afect' instead of 'affect'), translate its most likely intended meaning correctly.",
        "5. Provide ONLY the final, complete Russian translation. Do not include any comments, explanations, apologies, or introductory phrases like 'Вот перевод:'."
    ]

    rules_string = "\n".join(rules)

    prompt = (
        f"{system_instruction}\n\n"
        f"Follow these rules with extreme precision:\n{rules_string}\n\n"
        f"Translate the following English text:\n"
        f"'''{text_to_translate}'''"
    )

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={'model': 'llama3', 'prompt': prompt, 'stream': False},
            timeout=180
        )
        response.raise_for_status()

        return response.json()['response'].strip()

    except requests.exceptions.RequestException as e:
        print(f"Ollama connection error: {e}")
        return None


def process_and_save_word_pairs(source_doc, target_doc):
    if not nlp_en or not nlp_ru:
        print("SpaCy models not loaded. Skipping word analysis.")
        return
    POS_TO_IGNORE = ['ADP', 'CCONJ', 'DET', 'PUNCT', 'SPACE', 'PART', 'SCONJ', 'AUX', 'SYM', 'X']

>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
    def is_valid_token(token):
        if token.is_stop or token.pos_ in POS_TO_IGNORE or not token.text.strip():
            return False
        if len(token.text.strip()) == 1 and not token.text.strip().isalpha():
            return False
        return True

    spacy_source_doc = nlp_en(source_doc.text)
<<<<<<< HEAD
    source_lemma_counts = Counter(
        token.lemma_.lower() for token in spacy_source_doc if is_valid_token(token)
    )

    source_lemma_data = {
        token.lemma_.lower(): (token.text.lower(), token.pos_)
        for token in spacy_source_doc if is_valid_token(token)
    }

    for lemma, count in source_lemma_counts.items():
        word, pos = source_lemma_data[lemma]
        WordAnalysisEn.objects.update_or_create(
            document=source_doc,
            lemma=lemma,
            defaults={
                'word': word,
                'pos': pos,
                'frequency': count
            }
        )

    spacy_target_doc = nlp_ru(target_doc.text)
    target_lemma_counts = Counter(
        token.lemma_.lower() for token in spacy_target_doc if is_valid_token(token)
    )
    target_lemma_data = {
        token.lemma_.lower(): (token.text.lower(), token.pos_)
        for token in spacy_target_doc if is_valid_token(token)
    }

    for lemma, count in target_lemma_counts.items():
        word, pos = target_lemma_data[lemma]
        WordAnalysisRu.objects.update_or_create(
            document=target_doc,
            lemma=lemma,
            defaults={
                'word': word,
                'pos': pos,
                'frequency': count
            }
        )


def index_view(request):
    return render(request, 'translator_app/index.html')

=======
    en_word_objects_for_pairing = []
    for token in spacy_source_doc:
        if not is_valid_token(token): continue
        obj, created = WordAnalysisEn.objects.get_or_create(
            document=source_doc, word=token.text.lower(), lemma=token.lemma_, pos=token.pos_,
            defaults={'frequency': 1}
        )
        if not created: obj.frequency += 1; obj.save()
        en_word_objects_for_pairing.append(obj)
    spacy_target_doc = nlp_ru(target_doc.text)
    ru_word_objects_for_pairing = []
    for token in spacy_target_doc:
        if not is_valid_token(token): continue
        obj, created = WordAnalysisRu.objects.get_or_create(
            document=target_doc, word=token.text.lower(), lemma=token.lemma_, pos=token.pos_,
            defaults={'frequency': 1}
        )
        if not created: obj.frequency += 1; obj.save()
        ru_word_objects_for_pairing.append(obj)
    for en_word_obj, ru_word_obj in zip(en_word_objects_for_pairing, ru_word_objects_for_pairing):
        WordDictionary.objects.get_or_create(source_word=en_word_obj, target_word=ru_word_obj)


# ==========================================================
# 2. НОВЫЙ ПОТОК РАБОТЫ (АНАЛИЗ -> ПОДТВЕРЖДЕНИЕ -> РЕЗУЛЬТАТ)
# ==========================================================
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a

def manual_analysis_view(request):
    if request.method == 'POST':
        source_text = request.POST.get('source_text', '')
        if not source_text.strip():
            return render(request, 'translator_app/manual_analysis_page.html')
        doc = nlp_en(source_text)
        meaningful_tokens = [token for token in doc if token.pos_ not in ['PUNCT', 'SPACE', 'SYM']]
        pos_counts = Counter(token.pos_ for token in meaningful_tokens)
<<<<<<< HEAD
        grammar_info = {POS_TAGS_DESC.get(pos, pos): count for pos, count in pos_counts.items()}
        context = {'source_text': source_text, 'total_word_count': len(meaningful_tokens), 'grammar_info': grammar_info}
=======
        grammar_info = {
            POS_TAGS_DESC.get(pos, pos): count
            for pos, count in pos_counts.items()
        }
        context = {
            'source_text': source_text,
            'total_word_count': len(meaningful_tokens),
            'grammar_info': grammar_info,
        }
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
        return render(request, 'translator_app/analysis_confirmation_page.html', context)
    return render(request, 'translator_app/manual_analysis_page.html')


def execute_translation_view(request):
    if request.method == 'POST':
        source_text = request.POST.get('source_text', '')
        if not source_text: return redirect('manual_analysis_page')
<<<<<<< HEAD

        translation_result = translate_text_smart(source_text)
        if translation_result is None: return redirect('manual_analysis_page')

        target_text = translation_result['translation']
        word_map = translation_result['word_map']

=======
        target_text = translate_text_smart(source_text)
        if target_text is None: return redirect('manual_analysis_page')
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
        try:
            with transaction.atomic():
                source_doc = Document.objects.create(title="Ручной ввод (EN)", language='en', text=source_text)
                target_doc = Document.objects.create(title="Ручной перевод (RU)", language='ru', text=target_text)
                TranslationPair.objects.create(source_doc=source_doc, target_doc=target_doc)
<<<<<<< HEAD

                save_dictionary_and_pos(word_map, source_text, target_text)
=======
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
                process_and_save_word_pairs(source_doc, target_doc)
        except Exception as e:
            print(f"Error during saving: {e}")
            return redirect('manual_analysis_page')
<<<<<<< HEAD

=======
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
        return redirect('document_result', doc_id=source_doc.id)
    return redirect('index')


<<<<<<< HEAD
def file_analysis_view(request):
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('source_files')
        if not uploaded_files:
            return render(request, 'translator_app/file_upload.html')

        analyzed_files_data, files_for_session = [], []
        for file in uploaded_files:
            if not file.name.endswith('.txt'): continue
            source_text = file.read().decode('utf-8')
            if not source_text.strip(): continue

            doc = nlp_en(source_text)
            meaningful_tokens = [token for token in doc if token.pos_ not in ['PUNCT', 'SPACE', 'SYM']]
            pos_counts = Counter(token.pos_ for token in meaningful_tokens)
            grammar_info = {POS_TAGS_DESC.get(pos, pos): count for pos, count in pos_counts.items()}

            analyzed_files_data.append(
                {'filename': file.name, 'total_word_count': len(meaningful_tokens), 'grammar_info': grammar_info})
            files_for_session.append({'filename': file.name, 'text': source_text})

        request.session['files_to_translate'] = files_for_session
        context = {'analyzed_files': analyzed_files_data}
        return render(request, 'translator_app/file_analysis_confirmation_page.html', context)
    return render(request, 'translator_app/file_upload.html')


def execute_file_translation_view(request):
    if request.method == 'POST':
        files_to_translate = request.session.get('files_to_translate', [])
        if not files_to_translate: return redirect('index')

        processed_doc_ids = []
        try:
            with transaction.atomic():
                for file_data in files_to_translate:
                    source_text, filename = file_data['text'], file_data['filename']
                    translation_result = translate_text_smart(source_text)
                    if translation_result is None:
                        print(f"Warning: Translation failed for file {filename}. Skipping.")
                        continue

                    target_text = translation_result['translation']
                    word_map = translation_result['word_map']

                    source_doc = Document.objects.create(title=filename, language='en', text=source_text)
                    target_doc = Document.objects.create(title=f"Перевод {filename}", language='ru', text=target_text)
                    TranslationPair.objects.create(source_doc=source_doc, target_doc=target_doc)

                    save_dictionary_and_pos(word_map, source_text, target_text)
                    process_and_save_word_pairs(source_doc, target_doc)
                    processed_doc_ids.append(source_doc.id)
        except Exception as e:
            print(f"An error occurred during file processing: {e}")
            return redirect('file_upload_page')
        finally:
            if 'files_to_translate' in request.session:
                del request.session['files_to_translate']

        if len(processed_doc_ids) == 1:
            return redirect('document_result', doc_id=processed_doc_ids[0])
        elif len(processed_doc_ids) > 1:
            ids_string = ",".join(str(id) for id in processed_doc_ids)
            return redirect(f"{reverse('translation_results')}?ids={ids_string}")
    return redirect('index')


=======
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
def document_result_view(request, doc_id):
    source_doc = get_object_or_404(Document, pk=doc_id)
    pair = TranslationPair.objects.select_related('target_doc').filter(source_doc=source_doc).first()
    if not pair: return redirect('index')
<<<<<<< HEAD

    source_lemmas = WordAnalysisEn.objects.filter(document=source_doc).values_list('lemma', flat=True).distinct()
    word_map = DictionaryPair.objects.filter(
        source_lemma__lemma__in=source_lemmas
    ).select_related('source_lemma', 'target_lemma').order_by('source_lemma__lemma')

    context = {
        'source_doc': source_doc,
        'target_doc': pair.target_doc,
        'word_map': word_map,
        'translated_word_count': word_map.count(),
=======
    word_pairs = WordDictionary.objects.filter(
        source_word__document=source_doc
    ).select_related('source_word', 'target_word').order_by('-source_word__frequency', 'source_word__word')
    context = {
        'source_doc': source_doc,
        'target_doc': pair.target_doc,
        'word_pairs': word_pairs,
        'translated_word_count': word_pairs.count(),
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
        'pos_tags_desc': POS_TAGS_DESC,
    }
    return render(request, 'translator_app/document_result_page.html', context)


<<<<<<< HEAD
def translation_results_view(request):
    ids_string = request.GET.get('ids', '')
    translation_pairs = []
    if ids_string:
        try:
            doc_ids = [int(id) for id in ids_string.split(',')]
            translation_pairs = TranslationPair.objects.filter(source_doc_id__in=doc_ids).select_related('source_doc',
                                                                                                         'target_doc')
        except (ValueError, TypeError):
            pass
    context = {'translation_pairs': translation_pairs}
    return render(request, 'translator_app/translation_results.html', context)


def dictionary_list_view(request):
    """
    ОБНОВЛЕНО: Группирует все переводы по исходному слову для более чистого отображения.
    """

    all_pairs = DictionaryPair.objects.select_related('source_lemma', 'target_lemma').order_by('source_lemma__lemma')

    grouped_dictionary = {}

    for pair in all_pairs:
        source = pair.source_lemma
        target = pair.target_lemma

        if source not in grouped_dictionary:
            grouped_dictionary[source] = {
                'targets': [],
                'total_usage': 0
            }

        grouped_dictionary[source]['targets'].append(target)
        grouped_dictionary[source]['total_usage'] += pair.translation_count

    context = {'grouped_dictionary': grouped_dictionary}
    return render(request, 'translator_app/dictionary_list.html', context)
=======
# ==========================================================
# 3. СТАРЫЕ И ПРОЧИЕ ФУНКЦИИ
# ==========================================================
def index_view(request):
    return render(request, 'translator_app/index.html')
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a


def api_translate_view(request):
    if request.method != 'POST': return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    try:
        data = json.loads(request.body)
        text_to_translate = data.get('text', '')
        if not text_to_translate.strip(): return JsonResponse({'translated_text': ''})
<<<<<<< HEAD
        translation_result = translate_text_smart(text_to_translate)
        if translation_result is None:
            return JsonResponse({'error': 'Сервис перевода недоступен.'}, status=503)
        return JsonResponse({'translated_text': translation_result['translation']})
=======
        translated_text = translate_text_smart(text_to_translate)
        if translated_text is None:
            return JsonResponse({'error': 'Сервис перевода недоступен.'}, status=503)
        return JsonResponse({'translated_text': translated_text})
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"An unexpected error occurred in API: {e}")
        return JsonResponse({'error': 'An internal server error occurred'}, status=500)


<<<<<<< HEAD
def dictionary_detail_view(request, pk):
    pair = get_object_or_404(DictionaryPair.objects.select_related('source_lemma', 'target_lemma'), pk=pk)

    if request.method == 'POST':
        source_pos = request.POST.get('source_pos', '')
        target_pos = request.POST.get('target_pos', '')

        pair.source_lemma.pos = source_pos
        pair.source_lemma.save()

        pair.target_lemma.pos = target_pos
        pair.target_lemma.save()

        messages.success(request, 'Информация о паре успешно обновлена!')

        return redirect('dictionary_detail', pk=pair.pk)

    source_occurrences = WordAnalysisEn.objects.filter(lemma=pair.source_lemma.lemma)

    related_document_ids = source_occurrences.values_list('document_id', flat=True).distinct()
    related_documents = Document.objects.filter(pk__in=related_document_ids)

    usage_stats = []
    for doc in related_documents:

        frequency_in_doc = source_occurrences.filter(document=doc).first().frequency
        usage_stats.append({
            'document': doc,
            'frequency': frequency_in_doc
        })

    context = {
        'pair': pair,
        'usage_stats': usage_stats,
        'pos_tags_desc': POS_TAGS_DESC,
    }

    return render(request, 'translator_app/dictionary_detail.html', context)


def download_result_view(request, doc_id):
    """
    Генерирует и отдает для скачивания HTML-файл с результатами перевода.
    """
    source_doc = get_object_or_404(Document, pk=doc_id)
    pair = TranslationPair.objects.select_related('target_doc').filter(source_doc=source_doc).first()
    if not pair:
        return redirect('index')
    source_lemmas = WordAnalysisEn.objects.filter(document=source_doc).values_list('lemma', flat=True).distinct()
    word_map = DictionaryPair.objects.filter(
        source_lemma__lemma__in=source_lemmas
    ).select_related('source_lemma', 'target_lemma').order_by('source_lemma__lemma')
    html_content = render(request, 'translator_app/download_template.html', {
        'source_doc': source_doc,
        'target_doc': pair.target_doc,
        'word_map': word_map
    }).content

    response = HttpResponse(html_content, content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="translation_{doc_id}.html"'
    return response


def generate_syntax_tree_en_view(request, doc_id):
    """
    API-эндпоинт: генерирует HTML для синтаксического дерева английского текста.
    """
    if not nlp_en:
        return JsonResponse({'error': 'Модель spaCy для английского не загружена.'}, status=500)

    source_doc = get_object_or_404(Document, pk=doc_id)
    doc = nlp_en(source_doc.text)

    tree_html = spacy.displacy.render(doc, style="dep", jupyter=False)

    return JsonResponse({'tree_html': tree_html})


def generate_syntax_tree_ru_view(request, doc_id):
    """
    API-эндпоинт: генерирует HTML для синтаксического дерева русского текста.
    """
    if not nlp_ru:
        return JsonResponse({'error': 'Модель spaCy для русского не загружена.'}, status=500)

    source_doc = get_object_or_404(Document, pk=doc_id)
    pair = get_object_or_404(TranslationPair, source_doc=source_doc)
    target_doc = pair.target_doc

    doc = nlp_ru(target_doc.text)
    tree_html = spacy.displacy.render(doc, style="dep", jupyter=False)

    return JsonResponse({'tree_html': tree_html})


def help_view(request):
    """
    Отображает статичную страницу справки.
    """
    return render(request, 'translator_app/help_page.html')
=======
def file_upload_view(request):
    if request.method == 'POST':
        uploaded_files = request.FILES.getlist('source_files')
        if not uploaded_files: return redirect('file_upload_page')
        processed_pair_ids = []
        try:
            with transaction.atomic():
                for file in uploaded_files:
                    if not file.name.endswith('.txt'): continue
                    source_text = file.read().decode('utf-8')
                    if not source_text.strip(): continue
                    target_text = translate_text_smart(source_text)
                    if target_text is None: continue
                    source_doc = Document.objects.create(title=file.name, language='en', text=source_text)
                    target_doc = Document.objects.create(title=f"Перевод {file.name}", language='ru', text=target_text)
                    pair = TranslationPair.objects.create(source_doc=source_doc, target_doc=target_doc)
                    processed_pair_ids.append(pair.id)
                    process_and_save_word_pairs(source_doc, target_doc)
        except Exception as e:
            print(f"An error occurred during file processing: {e}")
            return redirect('file_upload_page')
        if processed_pair_ids:
            ids_string = ",".join(str(id) for id in processed_pair_ids)
            return redirect(f"{reverse('translation_results')}?ids={ids_string}")
        return redirect('index')
    return render(request, 'translator_app/file_upload.html')


def translation_results_view(request):
    ids_string = request.GET.get('ids', '')
    if ids_string:
        try:
            pair_ids = [int(id) for id in ids_string.split(',')]
            translation_pairs = TranslationPair.objects.filter(pk__in=pair_ids).select_related('source_doc',
                                                                                               'target_doc')
        except (ValueError, TypeError):
            translation_pairs = []
    else:
        translation_pairs = []
    context = {'translation_pairs': translation_pairs}
    return render(request, 'translator_app/translation_results.html', context)


def dictionary_list_view(request):
    all_pairs = WordDictionary.objects.select_related('source_word', 'target_word').order_by('source_word__word')
    context = {'pairs': all_pairs}
    return render(request, 'translator_app/dictionary_list.html', context)


def dictionary_detail_view(request, pk):
    pair = get_object_or_404(
        WordDictionary.objects.select_related('source_word', 'target_word', 'source_word__document'), pk=pk)
    context = {'pair': pair}
    return render(request, 'translator_app/dictionary_detail.html', context)
>>>>>>> c1adf90499b34d168a9f38aafc3b62df98a7456a
