import os
import time
import matplotlib.pyplot as plt
from django.test import TestCase
import django
from contextmanagerapp.views import analyze_text, extract_articles
import spacy

os.environ['DJANGO_SETTINGS_MODULE'] = 'contextmanager.settings'
django.setup()

class SpeedTest(TestCase):
    def setUp(self):
        # Проверка загрузки модели SpaCy
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except IOError:
            self.fail("SpaCy model 'en_core_web_sm' not found. Make sure it's installed in your test environment.")

        # Пути к существующим тестовым файлам
        self.file_paths = [
            "all_articles_5.txt",
            "all_articles_10.txt",
            "all_articles_15.txt",
            "all_articles_20.txt"
        ]
        self.article_counts = [5, 10, 15, 20]
        self.times = []

    def run_speed_test(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()

        start_time = time.time()
        articles = extract_articles(text)
        for article in articles:
            analyze_text(article["article_text"], article["metadata_text"])
        end_time = time.time()

        return end_time - start_time

    def test_speed(self):
        for file_path, count in zip(self.file_paths, self.article_counts):
            processing_time = self.run_speed_test(file_path)
            self.times.append((count, processing_time))
            print(f"Processing time for {file_path}: {processing_time:.4f} seconds")

        self.plot_results()

    def plot_results(self):
        counts, times = zip(*self.times)

        plt.figure(figsize=(10, 6))
        plt.plot(counts, times, marker='o', linestyle='-', color='b')
        plt.title('Зависимость времени обработки от количества статей')
        plt.xlabel('Количество статей')
        plt.ylabel('Время обработки (секунды)')
        plt.grid(True)
        plt.xticks(counts)
        plt.show()


if __name__ == '__main__':
    # Запуск тестов
    import unittest
    unittest.main()
