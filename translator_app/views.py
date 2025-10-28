# translator_app/views.py

import json
import requests
import spacy
from collections import Counter
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Document, TranslationPair, WordAnalysisEn, WordAnalysisRu, WordDictionary

# --- Загрузка моделей spaCy ---
try:
    nlp_en = spacy.load("en_core_web_sm")
    nlp_ru = spacy.load("ru_core_news_sm")
    print("✅ SpaCy models loaded successfully.")
except OSError:
    print("❌ SpaCy models not found. Please run the download commands.")
    nlp_en, nlp_ru = None, None
# -----------------------------

# Словарь для расшифровки тегов частей речи для вывода в шаблонах
POS_TAGS_DESC = {
    'NOUN': 'Существительное', 'VERB': 'Глагол', 'ADJ': 'Прилагательное',
    'ADV': 'Наречие', 'PROPN': 'Имя собственное', 'NUM': 'Числительное',
    'PRON': 'Местоимение', 'ADP': 'Предлог', 'AUX': 'Вспомогательный глагол',
    'CCONJ': 'Сочинительный союз', 'SCONJ': 'Подчинительный союз',
    'DET': 'Определитель (артикль)', 'INTJ': 'Междометие', 'PART': 'Частица',
    'PUNCT': 'Пунктуация', 'SYM': 'Символ', 'X': 'Другое', 'SPACE': 'Пробел'
}


# ==========================================================
# 1. ОСНОВНЫЕ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================================

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

    def is_valid_token(token):
        if token.is_stop or token.pos_ in POS_TO_IGNORE or not token.text.strip():
            return False
        if len(token.text.strip()) == 1 and not token.text.strip().isalpha():
            return False
        return True

    spacy_source_doc = nlp_en(source_doc.text)
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

def manual_analysis_view(request):
    if request.method == 'POST':
        source_text = request.POST.get('source_text', '')
        if not source_text.strip():
            return render(request, 'translator_app/manual_analysis_page.html')
        doc = nlp_en(source_text)
        meaningful_tokens = [token for token in doc if token.pos_ not in ['PUNCT', 'SPACE', 'SYM']]
        pos_counts = Counter(token.pos_ for token in meaningful_tokens)
        grammar_info = {
            POS_TAGS_DESC.get(pos, pos): count
            for pos, count in pos_counts.items()
        }
        context = {
            'source_text': source_text,
            'total_word_count': len(meaningful_tokens),
            'grammar_info': grammar_info,
        }
        return render(request, 'translator_app/analysis_confirmation_page.html', context)
    return render(request, 'translator_app/manual_analysis_page.html')


def execute_translation_view(request):
    if request.method == 'POST':
        source_text = request.POST.get('source_text', '')
        if not source_text: return redirect('manual_analysis_page')
        target_text = translate_text_smart(source_text)
        if target_text is None: return redirect('manual_analysis_page')
        try:
            with transaction.atomic():
                source_doc = Document.objects.create(title="Ручной ввод (EN)", language='en', text=source_text)
                target_doc = Document.objects.create(title="Ручной перевод (RU)", language='ru', text=target_text)
                TranslationPair.objects.create(source_doc=source_doc, target_doc=target_doc)
                process_and_save_word_pairs(source_doc, target_doc)
        except Exception as e:
            print(f"Error during saving: {e}")
            return redirect('manual_analysis_page')
        return redirect('document_result', doc_id=source_doc.id)
    return redirect('index')


def document_result_view(request, doc_id):
    source_doc = get_object_or_404(Document, pk=doc_id)
    pair = TranslationPair.objects.select_related('target_doc').filter(source_doc=source_doc).first()
    if not pair: return redirect('index')
    word_pairs = WordDictionary.objects.filter(
        source_word__document=source_doc
    ).select_related('source_word', 'target_word').order_by('-source_word__frequency', 'source_word__word')
    context = {
        'source_doc': source_doc,
        'target_doc': pair.target_doc,
        'word_pairs': word_pairs,
        'translated_word_count': word_pairs.count(),
        'pos_tags_desc': POS_TAGS_DESC,
    }
    return render(request, 'translator_app/document_result_page.html', context)


# ==========================================================
# 3. СТАРЫЕ И ПРОЧИЕ ФУНКЦИИ
# ==========================================================
def index_view(request):
    return render(request, 'translator_app/index.html')


def api_translate_view(request):
    if request.method != 'POST': return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    try:
        data = json.loads(request.body)
        text_to_translate = data.get('text', '')
        if not text_to_translate.strip(): return JsonResponse({'translated_text': ''})
        translated_text = translate_text_smart(text_to_translate)
        if translated_text is None:
            return JsonResponse({'error': 'Сервис перевода недоступен.'}, status=503)
        return JsonResponse({'translated_text': translated_text})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f"An unexpected error occurred in API: {e}")
        return JsonResponse({'error': 'An internal server error occurred'}, status=500)


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