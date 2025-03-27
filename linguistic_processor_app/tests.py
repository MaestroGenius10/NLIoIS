import os
import time
import matplotlib.pyplot as plt
from pathlib import Path
import django
from django.test import RequestFactory
import spacy

# Настройка окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'linguistic_processor.settings')
django.setup()

# Теперь можно импортировать модели и представления
from linguistic_processor_app.views import analyze_file

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Указываем на корень проекта


class AnalyzeFileSpeedTest:
    def __init__(self):
        # Проверка загрузки модели SpaCy
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except IOError:
            raise IOError(
                "SpaCy model 'en_core_web_sm' not found. Install it with: python -m spacy download en_core_web_sm")

        self.factory = RequestFactory()

        # Пути к тестовым файлам
        self.file_paths = [
            BASE_DIR / "lab_3" / "5.txt",
            BASE_DIR / "lab_3" / "10.txt",
            BASE_DIR / "lab_3" / "15.txt",
            BASE_DIR / "lab_3" / "20.txt",
            BASE_DIR / "lab_3" / "25.txt"
        ]

        # Метки для размеров файлов
        self.file_sizes = [5, 10, 15, 20, 25]
        self.times = []

    def prepare_test_file(self, file_path):
        """Читает тестовый файл и возвращает его содержимое"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def run_speed_test(self, file_path):
        """Замеряет время выполнения analyze_file для данного файла"""
        text = self.prepare_test_file(file_path)

        # Создаем тестовый запрос
        request = self.factory.get('/analyze-file/')
        request.session = {}
        request.session['file_content'] = text

        start_time = time.time()
        response = analyze_file(request)
        end_time = time.time()

        if response.status_code != 200:
            raise RuntimeError(f"Request failed with status {response.status_code}")

        return end_time - start_time

    def run_tests(self):
        """Основной метод для запуска тестов"""
        print("Starting speed tests...")

        for file_path, size in zip(self.file_paths, self.file_sizes):
            try:
                if not file_path.exists():
                    print(f" Test file not found: {file_path}")
                    continue

                print(f"\ Processing {file_path.name}...", end=" ", flush=True)
                processing_time = self.run_speed_test(file_path)
                self.times.append((size, processing_time))
                print(f"Done in {processing_time:.2f} seconds")
            except Exception as e:
                print(f" Error processing {file_path.name}: {str(e)}")
                continue

        if not self.times:
            print(" No timing data collected - check test files exist")
            return False

        self.plot_results()
        return True

    def plot_results(self):
        """Визуализация результатов"""
        sizes, times = zip(*self.times)

        plt.figure(figsize=(10, 6))
        plt.plot(sizes, times, marker='o', linestyle='-', color='b')
        plt.title('Время обработки файла в зависимости от количества предложений')
        plt.xlabel('Количество предложений')
        plt.ylabel('Время обработки файла (секунд)')
        plt.grid(True)
        plt.xticks(sizes)

        # Сохраняем график
        output_path = BASE_DIR / 'analyze_file_speed_test.png'
        plt.savefig(output_path)
        print(f" Graph saved to {output_path}")


if __name__ == '__main__':
    tester = AnalyzeFileSpeedTest()
    success = tester.run_tests()

    if not success:
        exit(1)