from django import forms
from .models import Sentence, Token


class SentenceForm(forms.ModelForm):
    class Meta:
        model = Sentence
        fields = ['text']


class TokenForm(forms.ModelForm):
    class Meta:
        model = Token
        fields = ['text', 'lemma', 'pos', 'dep', 'head_text', 'head_pos']
