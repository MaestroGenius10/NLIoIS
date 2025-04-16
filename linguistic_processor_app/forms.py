from django import forms
from .models import Sentence, Token
import json


class PrettyJSONWidget(forms.Textarea):
    def render(self, name, value, attrs=None, renderer=None):
        if value and isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
        if value and not isinstance(value, str):
            value = json.dumps(value, indent=2, ensure_ascii=False)
        return super().render(name, value, attrs, renderer)

class SentenceForm(forms.ModelForm):
    class Meta:
        model = Sentence
        fields = ['text']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'})
        }

class TokenForm(forms.ModelForm):
    definitions = forms.JSONField(
        required=False,
        widget=PrettyJSONWidget(attrs={
            'rows': 3,
            'class': 'form-control json-field'
        })
    )
    synonyms = forms.JSONField(
        required=False,
        widget=PrettyJSONWidget(attrs={
            'rows': 3,
            'class': 'form-control json-field'
        })
    )
    antonyms = forms.JSONField(
        required=False,
        widget=PrettyJSONWidget(attrs={
            'rows': 2,
            'class': 'form-control json-field'
        })
    )
    semantic_relations = forms.JSONField(
        required=False,
        widget=PrettyJSONWidget(attrs={
            'rows': 3,
            'class': 'form-control json-field'
        })
    )

    class Meta:
        model = Token
        fields = ['text', 'lemma', 'pos', 'dep', 'head_text', 'head_pos',
                 'definitions', 'synonyms', 'antonyms', 'semantic_relations']
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'lemma': forms.TextInput(attrs={'class': 'form-control'}),
            'pos': forms.TextInput(attrs={'class': 'form-control'}),
            'dep': forms.TextInput(attrs={'class': 'form-control'}),
            'head_text': forms.TextInput(attrs={'class': 'form-control'}),
            'head_pos': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_definitions(self):
        data = self.cleaned_data['definitions']
        return self._clean_json_field(data)

    def clean_synonyms(self):
        data = self.cleaned_data['synonyms']
        return self._clean_json_field(data)

    def clean_antonyms(self):
        data = self.cleaned_data['antonyms']
        return self._clean_json_field(data)

    def clean_semantic_relations(self):
        data = self.cleaned_data['semantic_relations']
        return self._clean_json_field(data)

    def _clean_json_field(self, data):
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                raise forms.ValidationError("Некорректный JSON формат")
        return data