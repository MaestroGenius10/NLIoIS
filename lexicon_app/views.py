from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from .models import Collocation
from .forms import CollocationForm
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from collections import defaultdict

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')
nltk.download('universal_tagset')


def extract_collocations(text):
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word.isalnum()]
    tokens = [word.lower() for word in tokens if word not in stopwords.words('english')]

    tagged = nltk.pos_tag(tokens, tagset='universal')

    collocations = defaultdict(list)

    for i in range(len(tagged)):
        for j in range(len(tagged)):
            if i == j:
                continue
            word1, pos1 = tagged[i]
            word2, pos2 = tagged[j]

            # Игнорируем артикли
            if pos1 == 'DET' or pos2 == 'DET':
                continue

            # Проверка правил словосочетаний
            if (pos1 == 'VERB' and pos2 in ['ADV', 'NOUN']) or \
               (pos1 == 'ADJ' and pos2 in ['NOUN']) or \
               (pos1 == 'ADV' and pos2 in ['ADJ', 'ADV']) or \
               (pos1 == 'PRON' and pos2 in ['VERB']) or \
               (pos1 == 'NUM' and pos2 == 'NOUN'):
                collocation = f"{word1} {word2}"
                collocation_type = determine_collocation_type(pos1, pos2)
                collocations[word1].append((word2, pos2, collocation, collocation_type, pos1))
            else:
                continue

    return collocations


def determine_collocation_type(pos1, pos2):
    if pos1 == 'VERB' and pos2 == 'ADV':
        return 'verb_adverb'
    elif pos1 == 'VERB' and pos2 == 'NOUN':
        return 'verb_noun'
    elif pos1 == 'ADJ' and pos2 == 'NOUN':
        return 'adjective_noun'
    elif pos1 == 'ADV' and pos2 == 'ADJ':
        return 'adverb_adjective'
    elif pos1 == 'ADV' and pos2 == 'ADV':
        return 'adverb_adverb'
    elif pos1 == 'PRON' and pos2 == 'VERB':
        return 'pronoun_verb'
    elif pos1 == 'NUM' and pos2 == 'NOUN':
        return 'numeral_noun'
    else:
        return 'other'


def index(request):
    if request.method == 'POST' and 'file' in request.FILES:
        file = request.FILES['file']
        fs = FileSystemStorage()

        # Проверяем, существует ли уже файл, чтобы избежать дублирования
        if not fs.exists(file.name):
            filename = fs.save(file.name, file)
        else:
            filename = file.name

        file_path = fs.path(filename)

        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        collocations = extract_collocations(text)
        sorted_collocations = dict(sorted(collocations.items()))

        return render(request, 'lexicon_app/collocation_list.html', {'collocations': sorted_collocations})

    return render(request, 'lexicon_app/index.html')


def save_collocations(request):
    if request.method == 'POST':
        collocations = request.POST.getlist('collocations')
        collocation_types = request.POST.getlist('collocation_types')
        words1 = request.POST.getlist('words1')
        pos1 = request.POST.getlist('pos1')
        words2 = request.POST.getlist('words2')
        pos2 = request.POST.getlist('pos2')

        for word1, pos1, word2, pos2, collocation, collocation_type in (
                zip(words1, pos1, words2, pos2, collocations, collocation_types)):
            # Проверяем, существует ли уже такое словосочетание в базе данных
            if not Collocation.objects.filter(
                word1=word1, part_of_speech1=pos1,
                word2=word2, part_of_speech2=pos2,
                collocation=collocation, collocation_type=collocation_type
            ).exists():
                Collocation.objects.create(
                    word1=word1, part_of_speech1=pos1,
                    word2=word2, part_of_speech2=pos2,
                    collocation=collocation, collocation_type=collocation_type
                )

        return redirect('index')


def view_dictionary(request):
    collocations = Collocation.objects.all().order_by('word1')
    collocations_dict = defaultdict(list)

    for collocation in collocations:
        collocations_dict[collocation.word1].append((collocation.word2,
                                                     collocation.part_of_speech2, collocation.collocation,
                                                     collocation.collocation_type, collocation.part_of_speech1,
                                                     collocation.id))

    return render(request, 'lexicon_app/dictionary.html', {'collocations': dict(collocations_dict)})


def edit_collocation(request, collocation_id):
    collocation = get_object_or_404(Collocation, id=collocation_id)
    if request.method == 'POST':
        form = CollocationForm(request.POST, instance=collocation)
        if form.is_valid():
            form.save()
            return redirect('view_dictionary')
    else:
        form = CollocationForm(instance=collocation)
    return render(request, 'lexicon_app/edit_collocation.html', {'form': form})


def delete_collocation(request, collocation_id):
    collocation = get_object_or_404(Collocation, id=collocation_id)
    if request.method == 'POST':
        collocation.delete()
        return redirect('view_dictionary')
    return render(request, 'lexicon_app/delete_collocation.html', {'collocation': collocation})


def search_collocations(request):
    word = request.GET.get('word', '')
    collocation_types = request.GET.getlist('collocation_types')

    # Получаем все словосочетания, содержащие искомое слово
    collocations = Collocation.objects.filter(word1=word) | Collocation.objects.filter(word2=word)

    # Фильтруем словосочетания по типу, если выбран
    if collocation_types:
        collocations = collocations.filter(collocation_type__in=collocation_types)

    # Группируем словосочетания по первому слову
    collocations_dict = defaultdict(list)
    for collocation in collocations:
        collocations_dict[collocation.word1].append(
            (collocation.word2, collocation.part_of_speech2, collocation.collocation,
             collocation.collocation_type, collocation.part_of_speech1, collocation.id)
        )

    # Получаем все возможные типы словосочетаний для фильтрации
    all_collocation_types = Collocation.objects.values_list('collocation_type', flat=True).distinct()

    return render(request, 'lexicon_app/search_collocations.html', {
        'collocations': dict(collocations_dict),
        'all_collocation_types': all_collocation_types,
        'selected_word': word,
        'selected_types': collocation_types
    })
