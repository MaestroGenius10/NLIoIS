import os
import time
import matplotlib.pyplot as plt
from django.test import TestCase
import django

# Переменная окружения для настроек Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'lexicon_project.settings'

django.setup()

# Необходимые модули после настройки окружения
from .views import extract_collocations

class SpeedTest(TestCase):
    def setUp(self):
        self.test_files_dir = 'test_files'
        os.makedirs(self.test_files_dir, exist_ok=True)

        # Создаем тестовые файлы с различным количеством слов
        self.file_sizes = [50, 100, 150, 200, 250]
        self.times = []

        # Предварительный запуск для "разогрева"
        self.warmup_size = 25
        self.create_test_file(f'warmup_{self.warmup_size}.txt', self.warmup_size)
        self.run_speed_test(f'warmup_{self.warmup_size}.txt')

        for size in self.file_sizes:
            self.create_test_file(f'test_{size}.txt', size)
            self.create_test_file(f'test_{size}.rtf', size, file_type='rtf')

    def create_test_file(self, filename, word_count, file_type='txt'):
        file_path = os.path.join(self.test_files_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(' '.join(['word'] * word_count))

    def run_speed_test(self, filename):
        file_path = os.path.join(self.test_files_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        start_time = time.time()
        extract_collocations(text)
        end_time = time.time()

        return end_time - start_time

    def test_speed(self):
        for size in self.file_sizes:
            txt_time = self.run_speed_test(f'test_{size}.txt')
            rtf_time = self.run_speed_test(f'test_{size}.rtf')
            self.times.append((size, txt_time, rtf_time))
            print(f"Processing time for test_{size}.txt: {txt_time:.4f} seconds")
            print(f"Processing time for test_{size}.rtf: {rtf_time:.4f} seconds")

        self.plot_results()

    def plot_results(self):
        txt_times = [time[1] for time in self.times]
        rtf_times = [time[2] for time in self.times]

        plt.plot(self.file_sizes, txt_times, label='TXT Files')
        plt.plot(self.file_sizes, rtf_times, label='RTF Files')
        plt.xlabel('Number of Words')
        plt.ylabel('Processing Time (seconds)')
        plt.title('Processing Time vs Number of Words')
        plt.legend()
        plt.grid(True)
        plt.show()

    def tearDown(self):
        # Удаляем тестовые файлы после завершения тестов
        for file_name in os.listdir(self.test_files_dir):
            file_path = os.path.join(self.test_files_dir, file_name)
            os.remove(file_path)
        os.rmdir(self.test_files_dir)

if __name__ == '__main__':
    # Запуск тестов
    import unittest
    unittest.main()
