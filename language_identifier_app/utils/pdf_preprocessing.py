import re
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from io import BytesIO


def extract_text_from_pdf(file):
    """
    Извлекает текст из PDF-файла, переданного как объект InMemoryUploadedFile.
    Безопасно обрабатывает повреждённые файлы и возвращает пустую строку, если чтение невозможно.
    """
    try:
        # Считываем файл один раз
        file_bytes = file.read()
        if not file_bytes:
            print(f"Файл {file.name} пустой")
            return ""

        # Создаем PdfReader из BytesIO
        reader = PdfReader(BytesIO(file_bytes))
        text = ""

        # Проходим по страницам
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        return text.strip()

    except PdfReadError as e:
        print(f"Ошибка чтения PDF {file.name}: {e}")
        return ""
    except Exception as e:
        print(f"Неизвестная ошибка при обработке {file.name}: {e}")
        return ""


def clean_text(text):
    """
    Очищает текст:
    - удаляет спецсимволы, цифры, пунктуацию;
    - приводит к нижнему регистру;
    - убирает лишние пробелы.
    """
    text = re.sub(r'[^a-zA-Zа-яА-ЯёЁ\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.lower().strip()
