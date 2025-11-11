import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from audiospeaker_app.models import SpeechRequest, RecognitionRequest  # <-- Добавили RecognitionRequest


class Command(BaseCommand):
    # Обновили описание
    help = 'Deletes ALL speech AND recognition requests from the database and ALL associated audio files.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Do not prompt for confirmation before deleting.',
        )

    def handle(self, *args, **options):
        """
        Основная логика команды.
        """
        # --- 1. Очистка базы данных ---
        self.stdout.write(self.style.NOTICE('\n--- Deleting Database Records ---'))

        # Удаляем записи о синтезе речи (TTS)
        tts_count, _ = SpeechRequest.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {tts_count} Text-to-Speech records.'))

        # Удаляем записи о распознавании речи (STT)
        stt_count, _ = RecognitionRequest.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {stt_count} Speech-to-Text records.'))

        self.stdout.write("-" * 40)

        # --- 2. Очистка медиафайлов ---
        self.stdout.write(self.style.NOTICE('--- Deleting Media Files ---'))

        # Формируем пути к папкам с аудио
        generated_audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio')
        uploaded_audio_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')

        # Удаляем папку со сгенерированными файлами (TTS)
        if os.path.exists(generated_audio_dir):
            try:
                shutil.rmtree(generated_audio_dir)
                self.stdout.write(self.style.SUCCESS(f'Successfully deleted directory: {generated_audio_dir}'))
                # Пересоздаем папку, чтобы приложение не сломалось
                os.makedirs(generated_audio_dir)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to delete {generated_audio_dir}. Reason: {e}'))
        else:
            self.stdout.write(self.style.WARNING(f"Directory '{generated_audio_dir}' not found. Skipping."))

        # Удаляем папку с загруженными файлами (STT)
        if os.path.exists(uploaded_audio_dir):
            try:
                shutil.rmtree(uploaded_audio_dir)
                self.stdout.write(self.style.SUCCESS(f'Successfully deleted directory: {uploaded_audio_dir}'))
                # Пересоздаем папку, чтобы приложение не сломалось
                os.makedirs(uploaded_audio_dir)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to delete {uploaded_audio_dir}. Reason: {e}'))
        else:
            self.stdout.write(self.style.WARNING(f"Directory '{uploaded_audio_dir}' not found. Skipping."))

        self.stdout.write("\n" + "-" * 40)
        self.stdout.write(self.style.SUCCESS('✅ Clean-up operation complete.'))