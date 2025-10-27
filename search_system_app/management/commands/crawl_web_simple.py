import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from search_system_app.models import Document
from urllib.parse import urlparse
from search_system_app.utils.preprocessing import preprocess_text

# Заранее подготовленные ссылки для автоматического краулинга
DEFAULT_URLS = [
"https://ru.wikipedia.org/wiki/Литература",
"https://ru.wikipedia.org/wiki/История_литературы",
"https://ru.wikipedia.org/wiki/Русская_литература",
"https://ru.wikipedia.org/wiki/Классическая_литература",
"https://ru.wikipedia.org/wiki/Художественная_литература",
"https://ru.wikipedia.org/wiki/Научная_литература",
"https://ru.wikipedia.org/wiki/Литература_США",
"https://ru.wikipedia.org/wiki/Литература_и_революция",
"https://ru.wikipedia.org/wiki/Индика_(литература)",
"https://ru.wikipedia.org/wiki/Литература!_Кругосветное_путешествие_по_миру_книг",
"https://ru.wikipedia.org/wiki/Музыка",
"https://ru.wikipedia.org/wiki/История_музыки",
"https://ru.wikipedia.org/wiki/Список_музыкальных_жанров,_направлений_и_стилей",
"https://ru.wikipedia.org/wiki/Поп-музыка",
"https://ru.wikipedia.org/wiki/Конкретная_музыка",
"https://ru.wikipedia.org/wiki/Музыка_России",
"https://ru.wikipedia.org/wiki/Тема_(музыка)",
"https://ru.wikipedia.org/wiki/Музыка_к_фильму",
"https://ru.wikipedia.org/wiki/Музыка_(рассказ)",
"https://ru.wikipedia.org/wiki/Музыка_(альбом)",
"https://ru.wikipedia.org/wiki/Кинематограф",
"https://ru.wikipedia.org/wiki/Фильм",
"https://ru.wikipedia.org/wiki/Киноискусство",
"https://ru.wikipedia.org/wiki/Кинематограф_России",
"https://ru.wikipedia.org/wiki/Кино-глаз",
"https://ru.wikipedia.org/wiki/2025_год_в_кино",
"https://ru.wikipedia.org/wiki/2023_год_в_кино",
"https://ru.wikipedia.org/wiki/Кино_(Делёз)",
"https://ru.wikipedia.org/wiki/Кино_(значения)",
"https://ru.wikipedia.org/wiki/Кино._Энциклопедический_словарь",
"https://ru.wikipedia.org/wiki/Искусство",
"https://ru.wikipedia.org/wiki/Изобразительное_искусство",
"https://ru.wikipedia.org/wiki/Живопись",
"https://ru.wikipedia.org/wiki/Скульптура",
"https://ru.wikipedia.org/wiki/Современное_искусство",
"https://ru.wikipedia.org/wiki/Искусство_Древней_Греции",
"https://ru.wikipedia.org/wiki/Теории_искусства",
"https://ru.wikipedia.org/wiki/Произведение_искусства",
"https://ru.wikipedia.org/wiki/Искусство_для_искусства",
"https://ru.wikipedia.org/wiki/Искусство_видеть",
]


class Command(BaseCommand):
    help = "Собирает документы с заранее заданных URL и пользовательских ссылок, сохраняя только основной текст статьи"

    def add_arguments(self, parser):
        parser.add_argument(
            '--urls', nargs='*', type=str, help='Дополнительные ссылки для краулинга'
        )
        parser.add_argument(
            '--only_user', action='store_true', help='Краулить только пользовательские ссылки'
        )

    def handle(self, *args, **options):
        # Получаем аргументы безопасно (чтобы не было KeyError)
        user_urls = options.get('urls', []) or []
        only_user = options.get('only_user', False)

        # Определяем, какие URL краулить
        if only_user:
            urls = user_urls  # только ссылки пользователя
        else:
            urls = DEFAULT_URLS + user_urls  # автоматический краулинг + доп. ссылки

        if not urls:
            self.stdout.write(self.style.WARNING("Нет ссылок для краулинга."))
            return

        for url in urls:
            try:
                self.stdout.write(f"Обрабатываю {url}...")
                headers = {
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/118.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "ru,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                self.stderr.write(f"Ошибка при запросе {url}: {e}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Убираем скрипты и стили
            for script_or_style in soup(['script', 'style']):
                script_or_style.decompose()

            # Извлекаем только текст из тегов <p>
            paragraphs = soup.find_all('p')
            text = ' '.join(p.get_text(strip=True) for p in paragraphs)
            length = len(text.split())

            title = soup.title.string if soup.title else url
            domain = urlparse(url).netloc

            tokens = preprocess_text(text)

            # Сохраняем документ в базу
            document, created = Document.objects.get_or_create(
                url=url,
                defaults={
                    'title': title,
                    'text': text,
                    'tokens': tokens,
                    'length': length,
                    'domain': domain
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Документ '{title[:50]}' сохранен."))
            else:
                self.stdout.write(self.style.WARNING(f"Документ '{title[:50]}' уже существует."))

