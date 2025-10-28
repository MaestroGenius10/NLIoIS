import requests
import json


def generate_keywords_via_ollama(doc_text: str, max_chars: int = 8000) -> str:
    """
    Генерирует реферат в виде ключевых слов через локальный Ollama (модель llama3).
    Возвращает результат в виде текста (иерархический список ключевых слов).
    """

    # Обрезаем длинные тексты, чтобы не перегружать модель
    if len(doc_text) > max_chars:
        doc_text = doc_text[:max_chars] + "..."

    prompt = f"""
Ты — эксперт по автоматическому реферированию текстов.
Проанализируй следующий документ и сформируй список ключевых слов и именных групп, отражающих основные темы.
Выведи результат в виде списка, при необходимости — иерархического (с отступами для уточнений). 
Ответ должен быть только на том языке, на котором входной документ

Пример вывода:
лазер
    лазерный луч
    синий лазер
    красный лазер
устройство

Документ:
\"\"\"{doc_text}\"\"\"
"""

    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        data = response.json()
        # Ollama возвращает {"model":"...", "created_at":"...", "response":"..."}
        if "response" in data:
            return data["response"].strip()

        # иногда может быть {"output":"..."}
        if "output" in data:
            return data["output"].strip()

        return json.dumps(data, ensure_ascii=False, indent=2)

    except requests.exceptions.RequestException as e:
        return f"Ошибка подключения к Ollama: {e}"
    except Exception as e:
        return f"Ошибка обработки ответа Ollama: {e}"
