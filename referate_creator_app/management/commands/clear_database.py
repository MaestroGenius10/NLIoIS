from django.core.management.base import BaseCommand
from django.apps import apps
from django.conf import settings
import os
import shutil


class Command(BaseCommand):
    help = "Полностью очищает базу данных и удаляет загруженные файлы."

    def handle(self, *args, **options):
        # Очищаем все таблицы
        for model in apps.get_models():
            model.objects.all().delete()
            self.stdout.write(f"🗑 Очищена таблица: {model.__name__}")

        uploads_path = os.path.join(settings.MEDIA_ROOT, "uploads")
        if os.path.exists(uploads_path):
            shutil.rmtree(uploads_path)
            os.makedirs(uploads_path, exist_ok=True)
            self.stdout.write("🧾 Папка 'uploads/' очищена.")

        self.stdout.write(self.style.SUCCESS("✅ База данных и файлы успешно очищены!"))
