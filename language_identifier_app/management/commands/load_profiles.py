from django.core.management.base import BaseCommand
from language_identifier_app.models import LanguageProfile
import json
from pathlib import Path


class Command(BaseCommand):
    help = "Загружает языковые профили (JSON) в базу данных"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            help="Путь к папке, где находятся файлы ru_corpus_1000.json и de_corpus_1000.json",
            default=".",
        )

    def handle(self, *args, **options):
        base_path = Path(options["path"])
        profiles = {
            "ru": base_path / "ru_corpus_1000.json",
            "de": base_path / "de_corpus_1000.json",
        }

        for lang, file_path in profiles.items():
            if not file_path.exists():
                self.stdout.write(self.style.ERROR(f"Файл не найден: {file_path}"))
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                word_freqs = json.load(f)

            short_freqs = {
                word: freq for word, freq in word_freqs.items() if len(word) <= 5
            }

            profile, created = LanguageProfile.objects.update_or_create(
                language=lang,
                defaults={
                    "word_frequencies": word_freqs,
                    "short_word_frequencies": short_freqs,
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Создан профиль для {profile.get_language_display()} ({len(word_freqs)} слов)"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"🔄 Обновлён профиль для {profile.get_language_display()} ({len(word_freqs)} слов)"
                    )
                )

        self.stdout.write(self.style.SUCCESS("\n🎉 Загрузка языковых профилей завершена!"))
