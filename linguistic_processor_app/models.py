from django.db import models
import json


class Sentence(models.Model):
    text = models.TextField()

    def __str__(self):
        return self.text[:50]


class Token(models.Model):
    sentence = models.ForeignKey(Sentence, related_name='tokens', on_delete=models.CASCADE)
    text = models.CharField(max_length=100)
    lemma = models.CharField(max_length=100)
    pos = models.CharField(max_length=10)
    dep = models.CharField(max_length=50)
    head_text = models.CharField(max_length=100)
    head_pos = models.CharField(max_length=10)

    # Поля для семантического анализа
    definitions = models.JSONField(default=list, blank=True)
    synonyms = models.JSONField(default=list, blank=True)
    antonyms = models.JSONField(default=list, blank=True)

    # Отдельные поля для каждого типа семантических отношений
    hypernyms = models.JSONField(default=list, blank=True)  # Более общие понятия
    hyponyms = models.JSONField(default=list, blank=True)  # Более конкретные понятия
    holonyms = models.JSONField(default=list, blank=True)  # Часть целого
    meronyms = models.JSONField(default=list, blank=True)  # Составные части
    entailments = models.JSONField(default=list, blank=True)  # Логические следствия
    causes = models.JSONField(default=list, blank=True)  # Причины
    also_sees = models.JSONField(default=list, blank=True)  # Связанные понятия

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        # Преобразуем строки в JSON при сохранении, если нужно
        json_fields = [
            'definitions', 'synonyms', 'antonyms',
            'hypernyms', 'hyponyms', 'holonyms', 'meronyms',
            'entailments', 'causes', 'also_sees'
        ]

        for field in json_fields:
            value = getattr(self, field)
            if isinstance(value, str):
                try:
                    setattr(self, field, json.loads(value))
                except json.JSONDecodeError:
                    setattr(self, field, [] if field.endswith('s') else {})

        super().save(*args, **kwargs)

    def get_semantic_relations(self):
        """Возвращает все семантические связи в виде словаря"""
        return {
            'hypernyms': self.hypernyms,
            'hyponyms': self.hyponyms,
            'holonyms': self.holonyms,
            'meronyms': self.meronyms,
            'entailments': self.entailments,
            'causes': self.causes,
            'also_sees': self.also_sees
        }


class TextAnalysisResult(models.Model):
    text = models.TextField()
    char_count = models.IntegerField()
    char_count_no_spaces = models.IntegerField()
    word_count = models.IntegerField()
    meaningful_word_count = models.IntegerField()
    unique_word_count = models.IntegerField()
    wateriness_percentage = models.FloatField()
    classical_toughness = models.FloatField()
    academic_toughness = models.FloatField()
    grammatical_errors = models.IntegerField()
    semantic_core = models.JSONField()

    def __str__(self):
        return f"Analysis of text starting with: {self.text[:20]}"
