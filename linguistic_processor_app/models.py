from django.db import models


class Sentence(models.Model):
    text = models.TextField()  # Полный текст предложения

    def __str__(self):
        return self.text[:50]  # Возвращает первые 50 символов предложения для отображения


class Token(models.Model):
    sentence = models.ForeignKey(Sentence, related_name='tokens', on_delete=models.CASCADE)
    text = models.CharField(max_length=100)  # Текст токена
    lemma = models.CharField(max_length=100)  # Лемма токена
    pos = models.CharField(max_length=10)  # Часть речи
    dep = models.CharField(max_length=50)  # Синтаксическая зависимость
    head_text = models.CharField(max_length=100)  # Текст главного слова
    head_pos = models.CharField(max_length=10)  # Часть речи главного слова

    def __str__(self):
        return self.text
