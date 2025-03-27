from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
import spacy
import tempfile
from spacy import displacy
from .models import Sentence, Token
from .forms import SentenceForm, TokenForm
# Загрузка модели spaCy
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


def upload_file(request):
    if request.method == 'POST' and 'file' in request.FILES:
        file = request.FILES['file']

        # Используем временный файл для обработки
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        # Чтение текста из временного файла
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Сохраняем текст в сессии для последующего анализа
        request.session['file_content'] = text

        return render(request, 'upload.html', {
            'file_name': file.name
        })
    return render(request, 'upload.html')


def analyze_file(request):
    if 'file_content' in request.session:
        text = request.session['file_content']

        # Обработка текста с помощью spaCy
        doc = nlp(text)

        # Подготовка данных для отображения
        sentences_data = []
        for sent in doc.sents:
            tokens_data = []
            for token in sent:
                # Пропускаем пунктуацию
                if token.pos_ == 'PUNCT':
                    continue

                # Получаем полное название зависимости
                dep_full = translations.get(token.dep_, token.dep_)
                tokens_data.append({
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_,
                    'dep': dep_full,
                    'head_text': token.head.text,
                    'head_pos': token.head.pos_
                })
            sentences_data.append({'text': sent.text, 'tokens': tokens_data})

        # Сохраняем данные в сессии для последующего сохранения
        request.session['sentences_data'] = sentences_data

        return render(request, 'results.html', {'sentences_data': sentences_data})
    return redirect('upload_file')


def save_results(request):
    if request.method == 'POST':
        sentences_data = request.session.get('sentences_data', [])
        print(sentences_data)
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
                    head_pos=token_data['head_pos']
                )
        return redirect('upload_file')
    return redirect('results')


def view_dictionary(request):
    # Извлечение всех предложений из базы данных
    sentences = Sentence.objects.all().order_by('text')

    # Подготовка данных для отображения
    sentences_data = []
    for sentence in sentences:
        tokens_data = []
        for token in sentence.tokens.all():
            tokens_data.append({
                'text': token.text,
                'lemma': token.lemma,
                'pos': token.pos,
                'dep': token.dep,
                'head_text': token.head_text,
                'head_pos': token.head_pos
            })
        sentences_data.append({'text': sentence.text, 'tokens': tokens_data, 'id': sentence.id})

    return render(request, 'dictionary.html', {'sentences_data': sentences_data,
                                               'translations': translations})


def view_syntax_tree(request, sentence_id):
    # Извлечение предложения из базы данных
    sentence = Sentence.objects.get(id=sentence_id)

    # Создание объекта Doc из текста предложения
    doc = nlp(sentence.text)

    # Замена сокращенных зависимостей на полные
    for token in doc:
        token.dep_ = translations.get(token.dep_, token.dep_)

    # Генерация HTML для синтаксического дерева с пользовательскими стилями
    html = displacy.render(doc, style="dep", page=True, options={
        "compact": True,
        "distance": 200,  # Увеличение расстояния между стрелками
        "color": "green",  # Пример изменения цвета стрелок
        "bg": "#f9f9f9"   # Пример изменения фона
    })

    return HttpResponse(html)


def edit_sentence(request, sentence_id):
    sentence = get_object_or_404(Sentence, id=sentence_id)
    tokens = sentence.tokens.all()

    if request.method == 'POST':
        sentence_form = SentenceForm(request.POST, instance=sentence)
        if sentence_form.is_valid():
            sentence_form.save()

            # Обработка токенов
            for token in tokens:
                token_form = TokenForm(request.POST, prefix=f'token-{token.id}', instance=token)
                if token_form.is_valid():
                    token_form.save()

            return redirect('view_dictionary')
    else:
        sentence_form = SentenceForm(instance=sentence)
        token_forms = [TokenForm(prefix=f'token-{token.id}', instance=token) for token in tokens]

    return render(request, 'edit_sentence.html', {
        'sentence_form': sentence_form,
        'token_forms': token_forms,
        'sentence': sentence
    })


def search_sentences(request):
    pos = request.GET.get('pos')
    dep_key = request.GET.get('dep')  # Например, "ROOT"

    # Преобразуем краткую роль (например, "ROOT") в полное название ("Root")
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
        # Фильтруем токены по заданным pos и dep
        tokens = sentence.tokens.all()
        if pos and dep:
            tokens = tokens.filter(pos=pos, dep=dep)
        elif pos:
            tokens = tokens.filter(pos=pos)
        elif dep:
            tokens = tokens.filter(dep=dep)

        tokens_data = []
        for token in tokens:
            tokens_data.append({
                'text': token.text,
                'lemma': token.lemma,
                'pos': token.pos,
                'dep': token.dep,
                'head_text': token.head_text,
                'head_pos': token.head_pos
            })

        if tokens_data:
            sentences_data.append({
                'text': sentence.text,
                'tokens': tokens_data,
                'id': sentence.id
            })

    return render(request, 'search_results.html', {
        'sentences_data': sentences_data,
        'pos': pos,
        'dep': dep_key  # Возвращаем исходное значение (например, "ROOT")
    })
