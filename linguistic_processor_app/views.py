from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
import spacy
from spacy import displacy
from .models import Sentence, Token, TextAnalysisResult
from .forms import SentenceForm, TokenForm
import nltk
from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
from collections import Counter
from striprtf.striprtf import rtf_to_text
import os
nltk.download('wordnet')
nltk.download('omw-1.4')

nlp = spacy.load("en_core_web_sm")

translations = {
    "ROOT": "Root",
    "nsubj": "Subject",
    "dobj": "Direct object",
    "iobj": "Indirect object",
    "pobj": "Object of preposition",
    "subj": "Nominal subject",
    "csubj": "Clausal subject",
    "attr": "Attribute",
    "agent": "Agent",
    "advcl": "Adverbial clause modifier",
    "advmod": "Adverbial modifier",
    "amod": "Adjectival modifier",
    "appos": "Appositional modifier",
    "aux": "Auxiliary",
    "auxpass": "Passive auxiliary",
    "cc": "Coordinating conjunction",
    "ccomp": "Clausal complement",
    "compound": "Compound word",
    "conj": "Conjunct",
    "dative": "Dative",
    "dep": "Unspecified dependency",
    "det": "Determiner",
    "expl": "Expletive",
    "intj": "Interjection",
    "mark": "Marker",
    "meta": "Meta modifier",
    "neg": "Negation modifier",
    "nmod": "Nominal modifier",
    "npadvmod": "Noun phrase as adverbial modifier",
    "nummod": "Numeric modifier",
    "oprd": "Object predicate",
    "parataxis": "Parataxis",
    "pcomp": "Prepositional complement",
    "poss": "Possession modifier",
    "preconj": "Preconjunct",
    "predet": "Pre-determiner",
    "prep": "Prepositional modifier",
    "prt": "Particle",
    "punct": "Punctuation",
    "quantmod": "Quantifier modifier",
    "relcl": "Relative clause modifier",
    "xcomp": "Open clausal complement"
}

groups = {
    "subject": {
        "nsubj",
        "csubj",
        "subj",
        "ROOT",
    },
    "predicate": {
        "attr",
        "aux",
        "auxpass",
        "cop",
        "xcomp",
    },
    "object": {
        "dobj",
        "iobj",
        "pobj",
        "oprd",
        "dative",
        "agent",
    },
    "modifier": {
        "amod",
        "appos",
        "compound",
        "det",
        "nmod",
        "nummod",
        "poss",
        "preconj",
        "predet",
        "quantmod",
        "relcl",
    },
    "adverbial": {
        "advcl",
        "advmod",
        "npadvmod",
        "punct",
        "mark",
        "cc",
        "prep",
        "parataxis",
        "dep",
    }
}


def upload_file(request):
    if request.method == 'POST' and 'file' in request.FILES:
        file = request.FILES['file']
        fs = FileSystemStorage()

        if not fs.exists(file.name):
            filename = fs.save(file.name, file)
        else:
            filename = file.name

        file_path = fs.path(filename)
        file_ext = os.path.splitext(filename)[1].lower()

        try:
            if file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()

            elif file_ext == '.rtf':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = rtf_to_text(f.read())

            else:
                return render(request, 'upload.html', {'error': 'Формат не поддерживается (только TXT, RTF, DOC).'})

            return render(request, 'upload.html', {'file_name': file.name, 'file_text': text})

        except Exception as e:
            return render(request, 'upload.html', {'error': f'Ошибка: {str(e)}'})

    return render(request, 'upload.html')


def analyze_file(request):
    if request.method == 'POST':
        text = request.POST.get("text", "")
        if text:
            doc = nlp(text)
            sentences_data = []

            wateriness_score = calculate_wateriness(text)

            for sent in doc.sents:
                tokens_data = []
                for token in sent:
                    if token.pos_ == 'PUNCT':
                        continue

                    dep_full = translations.get(token.dep_, token.dep_)
                    semantic_data = get_semantic_data(token.lemma_, token.pos_)

                    token_info = {
                        'text': token.text,
                        'lemma': token.lemma_,
                        'pos': token.pos_,
                        'dep': dep_full,
                        'head_text': token.head.text,
                        'head_pos': token.head.pos_,
                    }

                    if semantic_data:
                        token_info.update({
                            'definitions': semantic_data['definitions'],
                            'synonyms': dict(semantic_data['synonyms']),
                            'antonyms': semantic_data['antonyms'],
                            'hypernyms': semantic_data['hypernyms'],
                            'hyponyms': semantic_data['hyponyms'],
                            'holonyms': semantic_data['holonyms'],
                            'meronyms': semantic_data['meronyms'],
                            'entailments': semantic_data['entailments'],
                            'causes': semantic_data['causes'],
                            'also_sees': semantic_data['also_sees']
                        })

                    tokens_data.append(token_info)

                sentences_data.append({'text': sent.text, 'tokens': tokens_data})

            request.session['sentences_data'] = sentences_data
            return render(request, 'results.html', {
                'sentences_data': sentences_data,
                'translations': translations,
                'wateriness_score': wateriness_score  # Передаем водянистость в шаблон
            })
    return redirect('upload_file')


def calculate_wateriness(text):
    cleaned_text = re.sub(r'[^\w\s]', '', text).lower()
    words = cleaned_text.split()

    unique_words = set(words)
    total_words = len(words)
    unique_word_count = len(unique_words)

    word_freq = Counter(words)

    watery_threshold = 0.01 * total_words

    watery_phrases = [
        "as you know", "for example", "in fact", "it is worth noting", "it should be noted",
        "in other words", "on the other hand", "in conclusion", "to sum up", "in addition",
        "moreover", "furthermore", "in the first place", "first of all", "in the end",
        "to be honest", "to tell the truth", "in my opinion", "in my view", "as a result",
        "due to the fact that", "because of the fact that", "it goes without saying", "needless to say"
    ]

    watery_words = [word for word in words if word in watery_phrases or word_freq[word] > watery_threshold]

    wateriness_score = len(watery_words) / unique_word_count if unique_word_count > 0 else 0

    return wateriness_score*100


def save_results(request):
    if request.method == 'POST':
        sentences_data = request.session.get('sentences_data', [])
        for sentence_data in sentences_data:
            sentence = Sentence.objects.create(text=sentence_data['text'])
            for token_data in sentence_data['tokens']:
                Token.objects.create(
                    sentence=sentence,
                    text=token_data['text'],
                    lemma=token_data['lemma'],
                    pos=token_data['pos'],
                    dep=token_data['dep'],
                    head_text=token_data['head_text'],
                    head_pos=token_data['head_pos'],
                    definitions=token_data.get('definitions', []),
                    synonyms=token_data.get('synonyms', {}),
                    antonyms=token_data.get('antonyms', []),
                    hypernyms=token_data.get('hypernyms', []),
                    hyponyms=token_data.get('hyponyms', []),
                    holonyms=token_data.get('holonyms', []),
                    meronyms=token_data.get('meronyms', []),
                    entailments=token_data.get('entailments', []),
                    causes=token_data.get('causes', []),
                    also_sees=token_data.get('also_sees', [])
                )
        return redirect('upload_file')
    return redirect('results')


def visualize_syntax(request, sentence_id):
    sentence = get_object_or_404(Sentence, id=sentence_id)
    doc = nlp(sentence.text)

    options = {
        "compact": False,
        "distance": 120,
        "offset_x": 50,
        "bg": "#f9f9f9",
        "color": "#000000",
        "font": "Arial",
        "arrow_stroke": 2,
        "arrow_width": 8,
        "word_spacing": 30,
        "collapse_punct": True,
        "collapse_phrases": False,
    }

    # Подготовка стилей для разных групп
    spans = []
    for token in doc:
        # Пропускаем пунктуацию
        if token.is_punct:
            continue

        # Определяем стиль линии
        if token.dep_ in groups["subject"]:
            line_style = "solid"
            line_color = "#FF5733"  # оранжевый
        elif token.dep_ in groups["predicate"]:
            line_style = "double"
            line_color = "#33FF57"  # зеленый
        elif token.dep_ in groups["modifier"]:
            line_style = "wavy"
            line_color = "#3357FF"  # синий
        elif token.dep_ in groups["object"]:
            line_style = "dashed"
            line_color = "#F033FF"  # фиолетовый
        elif token.dep_ in groups["adverbial"]:
            line_style = "dotted"
            line_color = "#FF33F0"  # розовый
        else:
            line_style = "solid"
            line_color = "#AAAAAA"  # серый

        spans.append({
            "text": token.text,
            "style": f"text-decoration-line: underline; text-decoration-style: {line_style}; text-decoration-color: {line_color};"
        })

    # Генерация HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Графический синтаксический разбор</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .sentence {
                font-size: 24px;
                line-height: 2.5;
                text-align: center;
                margin: 30px 0;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
            .token {
                display: inline-block;
                margin: 0 3px;
                padding: 0 5px;
                position: relative;
                white-space: nowrap;
            }
            .legend {
                margin: 30px auto;
                padding: 15px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                max-width: 500px;
            }
            .legend-item {
                margin: 8px 0;
                padding: 5px;
                font-size: 16px;
            }
            .back-btn {
                display: block;
                margin: 20px auto;
                padding: 10px 20px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                text-decoration: none;
                text-align: center;
                width: 200px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="text-align: center;">Графический синтаксический разбор</h1>

            <div class="sentence">
    """

    # Добавляем токены с оформлением
    for span in spans:
        html += f'<span class="token" style="{span["style"]}">{span["text"]}</span>'

    # Добавляем легенду
    html += """
            </div>

            <div class="legend">
                <h3 style="text-align: center; margin-top: 0;">Легенда:</h3>
                <div class="legend-item" style="text-decoration-line: underline; text-decoration-style: solid; text-decoration-color: #FF5733;">
                    Подлежащее
                </div>
                <div class="legend-item" style="text-decoration-line: underline; text-decoration-style: double; text-decoration-color: #33FF57;">
                    Сказуемое
                </div>
                <div class="legend-item" style="text-decoration-line: underline; text-decoration-style: wavy; text-decoration-color: #3357FF;">
                    Определение
                </div>
                <div class="legend-item" style="text-decoration-line: underline; text-decoration-style: dashed; text-decoration-color: #F033FF;">
                    Дополнение
                </div>
                <div class="legend-item" style="text-decoration-line: underline; text-decoration-style: dotted; text-decoration-color: #FF33F0;">
                    Обстоятельство
                </div>
            </div>

            <a href="javascript:history.back()" class="back-btn">Вернуться назад</a>
        </div>
    </body>
    </html>
    """

    return HttpResponse(html)


def view_dictionary(request):

    sentences = Sentence.objects.all().order_by('text')

    sentences_data = []
    for sentence in sentences:
        tokens_data = []
        for token in sentence.tokens.all():
            token_data = {
                'text': token.text,
                'lemma': token.lemma,
                'pos': token.pos,
                'dep': token.dep,
                'head_text': token.head_text,
                'head_pos': token.head_pos,
                'definitions': token.definitions,
                'synonyms': token.synonyms,
                'antonyms': token.antonyms,
                'hypernyms': token.hypernyms,
                'hyponyms': token.hyponyms,
                'holonyms': token.holonyms,
                'meronyms': token.meronyms,
                'entailments': token.entailments,
                'causes': token.causes,
                'also_sees': token.also_sees,
            }
            tokens_data.append(token_data)

        sentences_data.append({
            'text': sentence.text,
            'tokens': tokens_data,
            'id': sentence.id
        })

    return render(request, 'dictionary.html', {
        'sentences_data': sentences_data,
        'translations': translations
    })


def view_syntax_tree(request, sentence_id):
    sentence = Sentence.objects.get(id=sentence_id)
    doc = nlp(sentence.text)

    for token in doc:
        token.dep_ = translations.get(token.dep_, token.dep_)

    # Упрощенные параметры визуализации без конфликтных типов
    html = displacy.render(doc, style="dep", page=True, options={
        "compact": True,
        "distance": 100,
        "offset_x": 50,
        "font": "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
        "arrow_stroke": 2,
        "arrow_width": 8,
        "word_spacing": 35,
        "color": "#166088",
        "bg": "#f4f4f9",
        "arrow_color": "#4a6fa5",
        "curve_style": "arc",
        "curve_radius": 1.0,
        "arrow_spacing": 15,
        "collapse_punct": True,
        "padding_top": 20,  # Числовое значение без 'px'
        "padding_bottom": 20,
        "align": "center",
        "font_size": 14,  # Числовое значение без 'px'
        "word_font_weight": 500,  # Числовое значение
        "under_arrows": True
    })

    # Добавляем кастомные стили для стрелок через замену в HTML
    html = html.replace(
        '.displacy-arrow { stroke: #000000; fill: none; }',
        '.displacy-arrow { stroke: #4a6fa5; fill: none; stroke-linecap: round; }'
    )
    html = html.replace(
        '.displacy-arrowhead { fill: #000000; }',
        '.displacy-arrowhead { fill: #4a6fa5; }'
    )

    return HttpResponse(html)


def edit_sentence(request, sentence_id):
    sentence = get_object_or_404(Sentence, id=sentence_id)
    tokens = sentence.tokens.all()

    if request.method == 'POST':
        sentence_form = SentenceForm(request.POST, instance=sentence)
        if sentence_form.is_valid():
            sentence_form.save()

            for token in tokens:
                token_form = TokenForm(
                    request.POST,
                    prefix=f'token-{token.id}',
                    instance=token
                )
                if token_form.is_valid():
                    token_form.save()
            return redirect('view_dictionary')
    else:
        sentence_form = SentenceForm(instance=sentence)
        token_forms = []
        for token in tokens:
            initial_data = {
                'definitions': token.definitions,
                'synonyms': token.synonyms,
                'antonyms': token.antonyms,
                'hypernyms': token.hypernyms,
                'hyponyms': token.hyponyms,
                'holonyms': token.holonyms,
                'meronyms': token.meronyms,
                'entailments': token.entailments,
                'causes': token.causes,
                'also_sees': token.also_sees
            }
            token_form = TokenForm(
                prefix=f'token-{token.id}',
                instance=token,
                initial=initial_data
            )
            token_forms.append(token_form)

    return render(request, 'edit_sentence.html', {
        'sentence_form': sentence_form,
        'token_forms': token_forms,
        'sentence': sentence
    })


def search_sentences(request):
    pos = request.GET.get('pos')
    dep_key = request.GET.get('dep')

    dep = translations.get(dep_key, dep_key) if dep_key else None

    sentences = Sentence.objects.all()
    if pos and dep:
        sentences = sentences.filter(tokens__pos=pos, tokens__dep=dep).distinct()
    elif pos:
        sentences = sentences.filter(tokens__pos=pos).distinct()
    elif dep:
        sentences = sentences.filter(tokens__dep=dep).distinct()

    sentences_data = []
    for sentence in sentences:

        tokens = sentence.tokens.all()
        if pos and dep:
            tokens = tokens.filter(pos=pos, dep=dep)
        elif pos:
            tokens = tokens.filter(pos=pos)
        elif dep:
            tokens = tokens.filter(dep=dep)

        tokens_data = []
        for token in tokens:
            token_info = {
                'text': token.text,
                'lemma': token.lemma,
                'pos': token.pos,
                'dep': token.dep,
                'head_text': token.head_text,
                'head_pos': token.head_pos,
                'definitions': token.definitions,
                'synonyms': token.synonyms,
                'antonyms': token.antonyms,
                'hypernyms': token.hypernyms,
                'hyponyms': token.hyponyms,
                'holonyms': token.holonyms,
                'meronyms': token.meronyms,
                'entailments': token.entailments,
                'causes': token.causes,
                'also_sees': token.also_sees,
            }
            tokens_data.append(token_info)

        if tokens_data:
            sentences_data.append({
                'text': sentence.text,
                'tokens': tokens_data,
                'id': sentence.id
            })

    return render(request, 'search_results.html', {
        'sentences_data': sentences_data,
        'pos': pos,
        'dep': dep_key
    })


POS_MAPPING = {
    'NOUN': 'n',
    'VERB': 'v',
    'ADJ': 'a',
    'ADV': 'r',
}


def get_semantic_data(lemma, pos_tag):

    wn_pos = POS_MAPPING.get(pos_tag)
    if not wn_pos:
        return None

    synsets = wn.synsets(lemma, pos=wn_pos)
    if not synsets:
        return None

    semantic_data = {
        'definitions': [],
        'synonyms': [],
        'antonyms': [],
        'hypernyms': [],
        'hyponyms': [],
        'holonyms': [],
        'meronyms': [],
        'entailments': [],
        'causes': [],
        'also_sees': []
    }

    for synset in synsets[:3]:

        definition_entry = {
            'definition': synset.definition(),
            'examples': synset.examples()[:2]
        }
        if definition_entry not in semantic_data['definitions']:
            semantic_data['definitions'].append(definition_entry)

        for lemma_obj in synset.lemmas():
            name = lemma_obj.name().replace('_', ' ')
            if name.lower() != lemma.lower():
                synonym_entry = (synset.name(), name)
                if synonym_entry not in semantic_data['synonyms']:
                    semantic_data['synonyms'].append(synonym_entry)

            for antonym in lemma_obj.antonyms():
                antonym_name = antonym.name().replace('_', ' ')
                if antonym_name not in semantic_data['antonyms']:
                    semantic_data['antonyms'].append(antonym_name)

        for hypernym in synset.hypernyms():
            if hypernym.name() not in semantic_data['hypernyms']:
                semantic_data['hypernyms'].append(hypernym.name())
        for hyponym in synset.hyponyms():
            if hyponym.name() not in semantic_data['hyponyms']:
                semantic_data['hyponyms'].append(hyponym.name())
        for holonym in synset.part_holonyms():
            if holonym.name() not in semantic_data['holonyms']:
                semantic_data['holonyms'].append(holonym.name())
        for meronym in synset.part_meronyms():
            if meronym.name() not in semantic_data['meronyms']:
                semantic_data['meronyms'].append(meronym.name())
        for entailment in synset.entailments():
            if entailment.name() not in semantic_data['entailments']:
                semantic_data['entailments'].append(entailment.name())
        for cause in synset.causes():
            if cause.name() not in semantic_data['causes']:
                semantic_data['causes'].append(cause.name())
        for also_see in synset.also_sees():
            if also_see.name() not in semantic_data['also_sees']:
                semantic_data['also_sees'].append(also_see.name())

    return semantic_data


def semantic_analyze(text):
    cleaned_text = re.sub(r'[^\w\s]', '', text).lower()
    words = word_tokenize(cleaned_text)

    char_count = len(text)
    char_count_no_spaces = len(text.replace(" ", ""))

    word_count = len(words)

    stop_words = set(stopwords.words('english'))
    meaningful_words = [word for word in words if word not in stop_words]
    meaningful_word_count = len(meaningful_words)

    unique_words = set(words)
    unique_word_count = len(unique_words)

    wateriness_score = calculate_wateriness(text)

    word_freq = Counter(words)
    most_common_word_count = word_freq.most_common(1)[0][1]
    classical_toughness = most_common_word_count ** 0.5

    academic_toughness = len(meaningful_words) / word_count

    grammatical_errors = 0

    word_freq_semantic_core = Counter(meaningful_words)
    semantic_core = {word: count for word, count in word_freq_semantic_core.items() if count > 1}

    return {
        'char_count': char_count,
        'char_count_no_spaces': char_count_no_spaces,
        'word_count': word_count,
        'meaningful_word_count': meaningful_word_count,
        'unique_word_count': unique_word_count,
        'wateriness_percentage': wateriness_score,
        'classical_toughness': classical_toughness,
        'academic_toughness': academic_toughness,
        'grammatical_errors': grammatical_errors,
        'semantic_core': semantic_core
    }


def semantic_analyze_file(request):
    if request.method == 'POST':
        text = request.POST.get("text", "")
        file = request.FILES.get("file", None)

        if not text and file:
            text = file.read().decode('utf-8')

        if text:
            # Выполняем анализ
            analysis_result = semantic_analyze(text)

            # Добавляем оригинальный текст в результаты
            analysis_result['text'] = text

            # Сортируем семантическое ядро по частоте
            sorted_semantic_core = dict(sorted(
                analysis_result['semantic_core'].items(),
                key=lambda item: item[1],
                reverse=True
            ))
            analysis_result['semantic_core'] = sorted_semantic_core

            request.session['analysis_result'] = analysis_result
            return render(request, 'semantic_analysis_results.html', {
                'analysis_result': analysis_result
            })

    return redirect('upload_file')


def save_results_semantic(request):
    if request.method == 'POST':
        analysis_result = request.session.get('analysis_result')
        if analysis_result:
            TextAnalysisResult.objects.create(
                text=analysis_result['text'],
                char_count=analysis_result['char_count'],
                char_count_no_spaces=analysis_result['char_count_no_spaces'],
                word_count=analysis_result['word_count'],
                meaningful_word_count=analysis_result['meaningful_word_count'],
                unique_word_count=analysis_result['unique_word_count'],
                wateriness_percentage=analysis_result['wateriness_percentage'],
                classical_toughness=analysis_result['classical_toughness'],
                academic_toughness=analysis_result['academic_toughness'],
                grammatical_errors=analysis_result['grammatical_errors'],
                semantic_core=analysis_result['semantic_core']
            )
        return redirect('upload_file')
    return redirect('semantic_analysis_results')


def all_semantic_analyses(request):
    analyses = TextAnalysisResult.objects.all().order_by('-id')
    return render(request, 'all_semantic_analyses.html', {'analyses': analyses})


def view_semantic_analysis(request, analysis_id):
    analysis = get_object_or_404(TextAnalysisResult, id=analysis_id)
    return render(request, 'semantic_analysis_results.html', {
        'analysis_result': {
            'text': analysis.text,
            'char_count': analysis.char_count,
            'char_count_no_spaces': analysis.char_count_no_spaces,
            'word_count': analysis.word_count,
            'meaningful_word_count': analysis.meaningful_word_count,
            'unique_word_count': analysis.unique_word_count,
            'wateriness_percentage': analysis.wateriness_percentage,
            'classical_toughness': analysis.classical_toughness,
            'academic_toughness': analysis.academic_toughness,
            'semantic_core': analysis.semantic_core
        }
    })
