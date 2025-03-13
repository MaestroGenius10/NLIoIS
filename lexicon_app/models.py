from django.db import models


class Collocation(models.Model):
    objects = None
    PART_OF_SPEECH_CHOICES = [
        ('NOUN', 'Noun'),
        ('VERB', 'Verb'),
        ('ADJ', 'Adjective'),
        ('ADV', 'Adverb'),
        ('PRON', 'Pronoun'),
        ('ADP', 'Preposition'),
        ('CONJ', 'Conjunction'),
        ('INTJ', 'Interjection'),
        ('DET', 'Article'),
        ('NUM', 'Numeral'),
        ('PRT', 'Participle'),
        ('GER', 'Gerund'),
        ('INF', 'Infinitive'),
    ]

    COLLOCATION_TYPE_CHOICES = [
        ('noun_adjective', 'Noun + Adjective'),
        ('noun_preposition', 'Noun + Preposition'),
        ('noun_verb', 'Noun + Verb'),
        ('verb_adverb', 'Verb + Adverb'),
        ('verb_noun', 'Verb + Noun'),
        ('verb_pronoun', 'Verb + Pronoun'),
        ('verb_preposition', 'Verb + Preposition'),
        ('adjective_noun', 'Adjective + Noun'),
        ('adjective_adverb', 'Adjective + Adverb'),
        ('adjective_preposition', 'Adjective + Preposition'),
        ('adverb_verb', 'Adverb + Verb'),
        ('adverb_adjective', 'Adverb + Adjective'),
        ('adverb_adverb', 'Adverb + Adverb'),
        ('pronoun_verb', 'Pronoun + Verb'),
        ('pronoun_preposition', 'Pronoun + Preposition'),
        ('preposition_noun', 'Preposition + Noun'),
        ('preposition_pronoun', 'Preposition + Pronoun'),
        ('preposition_verb', 'Preposition + Verb'),
        ('numeral_noun', 'Numeral + Noun'),
    ]

    word1 = models.CharField(max_length=100)
    part_of_speech1 = models.CharField(max_length=4, choices=PART_OF_SPEECH_CHOICES)
    word2 = models.CharField(max_length=100)
    part_of_speech2 = models.CharField(max_length=4, choices=PART_OF_SPEECH_CHOICES)
    collocation = models.CharField(max_length=200)
    collocation_type = models.CharField(max_length=50, choices=COLLOCATION_TYPE_CHOICES)

    def __str__(self):
        return self.collocation
