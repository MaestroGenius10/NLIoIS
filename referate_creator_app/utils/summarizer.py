import re
import math
from collections import Counter, defaultdict
from typing import List, Tuple
import string

# Наборы стоп-слов (упрощённые — можно расширить)
RUSSIAN_STOPWORDS = {
    "и", "в", "во", "не", "на", "с", "что", "он", "она", "они", "как", "это",
    "по", "из", "за", "от", "для", "я", "ты", "мы", "вы", "к", "до", "о", "об",
    "его", "ее", "их", "а", "но", "же", "если", "то", "или", "быть", "бы"
}
ENGLISH_STOPWORDS = {
    "the", "and", "is", "in", "it", "of", "to", "a", "an", "for", "on", "with",
    "that", "this", "as", "are", "was", "were", "be", "by", "or", "not"
}

WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9\-']+", flags=re.UNICODE)


def split_sentences(text: str) -> List[Tuple[str,int,int]]:
    """
    Разбивает текст на предложения. Возвращает список (sentence_text, start_idx, end_idx).
    Простая реализация на основе регулярных выражений.
    """
    # используем split по окончанию предложения (точка, вопрос, воскл) с учётом сокращений
    # простая версия:
    pieces = re.split(r'(?<=[\.\!\?])\s+', text)
    res = []
    pos = 0
    for p in pieces:
        if p.strip():
            start = text.find(p, pos)
            end = start + len(p)
            res.append((p.strip(), start, end))
            pos = end
    return res


def split_paragraphs(text: str) -> List[Tuple[str,int,int]]:
    """
    Разбивает на абзацы (пустая строка как разделитель). Возвращает (para_text, start, end).
    """
    parts = re.split(r'\n\s*\n', text)
    res = []
    pos = 0
    for p in parts:
        if p.strip():
            start = text.find(p, pos)
            end = start + len(p)
            res.append((p.strip(), start, end))
            pos = end
    return res


def tokenize(text: str, lang: str = "auto") -> List[str]:
    """
    Токенизация: возвращает список слов в нижнем регистре.
    Исключаем токены, состоящие только из латинских букв/чисел, если нужно — фильтруем.
    """
    tokens = WORD_RE.findall(text)
    tokens = [t.lower() for t in tokens]
    return tokens


def is_latin_or_number(token: str) -> bool:
    # если любой латинский символ или цифра — считаем латиницей/числом
    return bool(re.search(r'[A-Za-z]', token)) or bool(re.search(r'\d', token))


def build_corpus_statistics(doc_texts: List[str]) -> Tuple[List[Counter], Counter, int]:
    """
    Возвращает:
      - list_doc_counters: список Counter(term->count) для каждого документа
      - df_counter: Counter(term->document_freq) по всем документам
      - N: количество документов
    """
    list_doc_counters = []
    df_counter = Counter()
    for text in doc_texts:
        tokens = [t for t in tokenize(text) if t.strip()]
        cnt = Counter(tokens)
        list_doc_counters.append(cnt)
        # увеличиваем df для уникальных слов в документе
        for term in cnt.keys():
            df_counter[term] += 1
    return list_doc_counters, df_counter, len(doc_texts)


def compute_modified_tfidf_for_doc(doc_text: str, df_counter: Counter, N_docs: int,
                                   stopwords=set(), ignore_latin=True) -> dict:
    """
    Возвращает словарь term->weight_in_doc (модифицированный TF*IDF для документа),
    а также max_tf_in_doc (для нормировок).
    Модификация:
      weight_t = (tf_t_in_doc / max_tf_in_doc) * log( (N_docs + 1) / (df_t + 1) )
    """
    tokens = [t for t in tokenize(doc_text) if t.strip()]
    # фильтрация
    filtered = []
    for t in tokens:
        if ignore_latin and is_latin_or_number(t):
            continue
        if t in stopwords:
            continue
        filtered.append(t)
    doc_counter = Counter(filtered)
    if not doc_counter:
        return {}
    max_tf = max(doc_counter.values())
    weights = {}
    for term, tf in doc_counter.items():
        df = df_counter.get(term, 0)
        idf = math.log((N_docs + 1) / (df + 1)) + 1.0  # +1 для сглаживания
        weights[term] = (tf / max_tf) * idf
    return weights


def sentence_weight(sentence: str, doc_text: str, para_bounds: List[Tuple[str,int,int]],
                    sent_start: int, term_doc_weights: dict, base_term_scores: Counter) -> float:
    """
    Вычисление веса предложения Si.
    Формула (одна из возможных реализаций на основании описания):
        W(Si) = F_terms(Si) * F_pos_doc(Si) * F_pos_para(Si) * F_len(Si)
    Где:
      F_terms(Si) = суммарный вклад терминов в предложении (сумма весов терминов из term_doc_weights умножённая на частоту в предложении)
      F_pos_doc(Si) = 1 - BD/|D|  (BD — количество символов до начала Si в документе)
      F_pos_para(Si) = 1 - BP/|P|  (BP — количество символов до Si в абзаце)
      F_len(Si) = 1 + log(1 + num_words_in_sentence) — поощряем информативные предложения
    Возвращаем произведение (и защищаем от нулей).
    """
    D_len = max(1, len(doc_text))
    BD = max(0, sent_start)
    F_pos_doc = 1.0 - (BD / D_len)
    if F_pos_doc <= 0:
        F_pos_doc = 0.01

    # найдём абзац содержащий предложение
    BP = 0
    P_len = 1
    for para_text, pstart, pend in para_bounds:
        if pstart <= sent_start < pend:
            BP = sent_start - pstart
            P_len = max(1, len(para_text))
            break
    F_pos_para = 1.0 - (BP / P_len)
    if F_pos_para <= 0:
        F_pos_para = 0.01

    # термины в предложении
    tokens = [t for t in tokenize(sentence) if t.strip()]
    term_counts = Counter()
    for t in tokens:
        term_counts[t] += 1

    F_terms = 0.0
    for term, cnt in term_counts.items():
        w = term_doc_weights.get(term, 0.0)
        F_terms += w * cnt

    # если нет терминов — малый вклад
    if F_terms <= 0:
        F_terms = 0.001

    num_words = len(tokens)
    F_len = 1.0 + math.log(1 + num_words)

    weight = F_terms * F_pos_doc * F_pos_para * F_len
    return weight


def extract_summary_by_sentences(doc_text: str, term_doc_weights: dict,
                                 top_k_sentences: int = 10) -> str:
    """
    Основная процедура: разбить на предложения, вычислить веса, выбрать top_k_sentences,
    вернуть текст-реферат из выбранных предложений в порядке оригинального текста.
    """
    sents = split_sentences(doc_text)
    paras = split_paragraphs(doc_text)
    sent_infos = []
    # precompute base term scores if needed
    base_term_scores = Counter()
    for term, w in term_doc_weights.items():
        base_term_scores[term] = w

    for sent_text, start, end in sents:
        w = sentence_weight(sent_text, doc_text, paras, start, term_doc_weights, base_term_scores)
        sent_infos.append({"text": sent_text, "start": start, "weight": w})

    # выбрать top_k по весу, затем отсортировать по start (порядок в тексте)
    sent_infos_sorted = sorted(sent_infos, key=lambda x: x["weight"], reverse=True)[:top_k_sentences]
    sent_infos_sorted = sorted(sent_infos_sorted, key=lambda x: x["start"])
    summary = " ".join([s["text"] for s in sent_infos_sorted])
    return summary
