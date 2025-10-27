import json
import re
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from time import sleep

# --- Настройки ---
RU_URL = "https://russianenthusiast.com/russian-vocab/top-1000-russian-words/"
DE_URL = "https://strommeninc.com/1000-most-common-german-words-frequency-vocabulary/"
OUT_RU = "ru_corpus_1000.json"
OUT_DE = "de_corpus_1000.json"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; profile-generator/1.0)"}

SLEEP_BETWEEN_REQUESTS = 0.5

# --- Регэкспы для фильтрации слов целевого языка ---
RE_RU = re.compile(r'^[а-яё\-]+$', re.IGNORECASE)  # только кириллица и дефис
RE_DE = re.compile(r'^[a-zäöüß\-]+$', re.IGNORECASE)  # латиница + немецкие буквы + дефис


def fetch_soup(url):
    r = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def extract_russian_words(soup, max_words=1000):
    words = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        for td in tds[:2]:
            text = td.get_text(strip=True).lower()
            text = re.sub(r'\(.*?\)', '', text).strip()
            text = re.sub(r'[^а-яё\-]', '', text)
            if len(text) > 0 and RE_RU.match(text):
                words.append(text)
                break
        if len(words) >= max_words:
            break

    if len(words) < max_words:
        for li in soup.find_all(["li", "p"]):
            text = li.get_text(strip=True).lower()
            text = re.sub(r'\(.*?\)', '', text).strip()
            text = re.sub(r'[^а-яё\-]', '', text)
            if len(text) > 0 and RE_RU.match(text):
                words.append(text)
            if len(words) >= max_words:
                break
    seen = set()
    final = []
    for w in words:
        if w not in seen:
            seen.add(w)
            final.append(w)
        if len(final) >= max_words:
            break
    return final


def extract_german_words(soup, max_words=1000):
    words = []
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td")
        if not tds:
            continue
        for td in tds[:3]:
            text = td.get_text(strip=True).lower()
            text = re.sub(r'\(.*?\)', '', text).strip()
            text = re.sub(r'[^a-zäöüß\-]', '', text)
            if len(text) > 0 and RE_DE.match(text):
                if text in ("german", "word", "number", "rank", "and", "the"):
                    continue
                words.append(text)
                break
        if len(words) >= max_words:
            break

    if len(words) < max_words:
        for li in soup.find_all(["li", "p"]):
            text = li.get_text(strip=True).lower()
            text = re.sub(r'\(.*?\)', '', text).strip()
            text = re.sub(r'[^a-zäöüß\-]', '', text)
            if len(text) > 0 and RE_DE.match(text):
                if text in ("german", "word", "number", "rank", "and", "the"):
                    continue
                words.append(text)
            if len(words) >= max_words:
                break

    seen = set()
    final = []
    for w in words:
        if w not in seen:
            seen.add(w)
            final.append(w)
        if len(final) >= max_words:
            break
    return final


def make_frequency_dict(words):
    n = len(words)
    if n == 0:
        return {}
    raw = [(w, n - i) for i, w in enumerate(words)]
    total = sum(weight for _, weight in raw)
    freqs = {w: round(weight / total, 8) for w, weight in raw}
    return freqs


def save_json(data, filename):
    p = Path(filename)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ {filename} сохранён — слов: {len(data)}")


def build_ru(max_words=1000):
    print("Загружаем RU:", RU_URL)
    soup = fetch_soup(RU_URL)
    words = extract_russian_words(soup, max_words=max_words)
    print(f"Найдено слов (RU): {len(words)}")
    if len(words) < max_words:
        print("Внимание: найдено меньше слов, чем запрошено. Можно добавить альтернативные источники.")
    freqs = make_frequency_dict(words)
    save_json(freqs, OUT_RU)


def build_de(max_words=1000):
    print("Загружаем DE:", DE_URL)
    soup = fetch_soup(DE_URL)
    words = extract_german_words(soup, max_words=max_words)
    print(f"Найдено слов (DE): {len(words)}")
    if len(words) < max_words:
        print("Внимание: найдено меньше слов, чем запрошено. Можно добавить альтернативные источники.")
    freqs = make_frequency_dict(words)
    save_json(freqs, OUT_DE)


def main():
    build_ru()
    sleep(SLEEP_BETWEEN_REQUESTS)
    build_de()
    print("Готово.")


if __name__ == "__main__":
    main()