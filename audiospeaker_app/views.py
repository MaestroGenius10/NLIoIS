import os
import json
import uuid

from django.shortcuts import render
from django.http import JsonResponse, FileResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError

from .models import SpeechRequest, RecognitionRequest
ELEVENLABS_API_KEY = settings.ELEVENLABS_API_KEY
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)


def index(request):
    """
    Отображает главную страницу приложения.
    """
    return render(request, 'audiospeaker_app/index.html')


@csrf_exempt
@require_POST
def synthesize_speech_api(request):
    """
    Обрабатывает AJAX POST-запрос на синтез речи с использованием ElevenLabs API.
    """
    if not ELEVENLABS_API_KEY:
        return JsonResponse({'error': 'ElevenLabs API Key не настроен на сервере.'}, status=503)

    try:
        data = json.loads(request.body)
        text_content = data.get('text_content', '').strip()
        voice_id = data.get('voice_id')
        stability = data.get('stability', 0.75)
        similarity_boost = data.get('similarity_boost', 0.75)
        model_id = data.get('model_id', 'eleven_multilingual_v2')

        if not text_content:
            return JsonResponse({'error': 'Текст для озвучивания не может быть пустым.'}, status=400)
        if not voice_id:
            return JsonResponse({'error': 'ID голоса не указан.'}, status=400)
        audio = client.text_to_speech.convert(
            voice_id=voice_id,
            model_id=model_id,
            text=text_content,
            voice_settings={
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
            output_format="mp3_44100_128"
        )

        audio_filename = f"speech_{uuid.uuid4()}.mp3"
        audio_sub_path = os.path.join('audio', audio_filename)
        audio_full_path = os.path.join(settings.MEDIA_ROOT, audio_sub_path)

        os.makedirs(os.path.dirname(audio_full_path), exist_ok=True)

        with open(audio_full_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        speech_request = SpeechRequest.objects.create(
            text_content=text_content,
            audio_file_path=audio_sub_path,
            voice_id=voice_id,
            voice_settings={'stability': stability, 'similarity_boost': similarity_boost},
            model_id=model_id
        )

        audio_url = settings.MEDIA_URL + audio_sub_path
        return JsonResponse({'audio_url': audio_url, 'request_id': speech_request.id})

    except ApiError as elevenlabs_err:
        print(f"Ошибка ElevenLabs API: {elevenlabs_err}")
        return JsonResponse({'error': f'Ошибка от ElevenLabs: {str(elevenlabs_err)}'}, status=502)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Некорректный JSON в запросе.'}, status=400)
    except Exception as e:
        print(f"Неизвестная ошибка при синтезе речи: {e}")
        return JsonResponse({'error': f'Внутренняя ошибка сервера: {str(e)}'}, status=500)


@require_GET
def text_to_speech_view(request):
    """
    Отображает страницу для озвучивания текста.
    Загружает список доступных голосов ElevenLabs, модель используется статически.
    """
    available_voices = []
    error_message = None

    if ELEVENLABS_API_KEY:
        try:
            elevenlabs_voices_response = client.voices.get_all()
            for voice in elevenlabs_voices_response.voices:
                if voice.category in ['premade', 'cloned']:
                    available_voices.append({
                        'voice_id': voice.voice_id,
                        'name': voice.name,
                        'category': voice.category,
                        'labels': voice.labels,
                    })

        except ApiError as elevenlabs_err:
            error_message = f"Не удалось загрузить голоса из ElevenLabs: {elevenlabs_err}"
            print(f"Ошибка ElevenLabs API при получении голосов: {elevenlabs_err}")
        except Exception as e:
            error_message = "Произошла внутренняя ошибка при получении голосов."
            print(f"Общая ошибка при получении голосов ElevenLabs: {e}")

    context = {
        'title': 'Озвучить текст',
        'available_voices': available_voices,
        'default_voice_id': 'EXAVITQu4vr4xnSDxYa4',
        'default_model_id': 'eleven_multilingual_v2',
        'error_message': error_message
    }
    return render(request, 'audiospeaker_app/text_to_speech.html', context)


@require_GET
def speech_history_view(request):
    """
    Отображает страницу с историей всех озвученных текстов.
    Также загружает имена голосов из API для корректного отображения.
    """
    history_entries = SpeechRequest.objects.all().order_by('-created_at')
    voices_map = {}
    error_message = None

    if ELEVENLABS_API_KEY:
        try:
            all_voices = client.voices.get_all()

            voices_map = {voice.voice_id: voice.name for voice in all_voices.voices}

        except ApiError as e:
            error_message = "Не удалось загрузить имена голосов из ElevenLabs. Будут показаны ID."
            print(f"Ошибка при загрузке голосов для истории: {e}")

    for entry in history_entries:
        entry.voice_name = voices_map.get(entry.voice_id, entry.voice_id)

    context = {
        'title': 'История озвучиваний',
        'history_entries': history_entries,
        'error_message': error_message,
        'MEDIA_URL': settings.MEDIA_URL  # <-- ВОТ ЭТА СТРОКА
    }
    return render(request, 'audiospeaker_app/speech_history.html', context)


@require_GET
def help_view(request):
    """
    Отображает справочную страницу со всеми доступными голосами и их
    описанием на русском языке.
    """
    voices_info = []
    error_message = None

    translation_map = {
        'gender': {
            'male': 'Мужской',
            'female': 'Женский'
        },
        'age': {
            'young': 'Молодой',
            'middle_aged': 'Средних лет',
            'old': 'Пожилой'
        },
        'accent': {
            'american': 'американский',
            'british': 'британский',
            'australian': 'австралийский',
            'indian': 'индийский',
            'african': 'африканский'
        },
        'description': {
            'calm': 'спокойный',
            'narration': 'повествование',
            'conversational': 'разговорный',
            'deep': 'глубокий',
            'soft': 'мягкий',
            'energetic': 'энергичный'
        }
    }

    if ELEVENLABS_API_KEY:
        try:
            all_voices = client.voices.get_all()

            for voice in all_voices.voices:
                if voice.category not in ['premade', 'cloned']:
                    continue

                labels = voice.labels
                russian_description_parts = []

                if 'gender' in labels:
                    russian_description_parts.append(translation_map['gender'].get(labels['gender'], ''))

                if 'age' in labels:
                    russian_description_parts.append(translation_map['age'].get(labels['age'], ''))

                if 'accent' in labels:
                    russian_description_parts.append(
                        translation_map['accent'].get(labels['accent'], labels['accent']) + " акцент")

                if 'description' in labels:
                    style_parts = [translation_map['description'].get(d.strip(), d.strip()) for d in
                                   labels['description'].split(',')]
                    if style_parts:
                        russian_description_parts.append("Стиль: " + ", ".join(style_parts))

                final_description = ". ".join(filter(None, russian_description_parts)).capitalize()

                voices_info.append({
                    'name': voice.name,
                    'category': voice.category.replace('premade', 'Стандартный').replace('cloned', 'Клонированный'),
                    'description': final_description if final_description else "Общее назначение"
                })

        except ApiError as e:
            error_message = "Не удалось загрузить информацию о голосах из ElevenLabs."
            print(f"Ошибка при загрузке голосов для страницы помощи: {e}")

    context = {
        'title': 'Справка по голосам',
        'voices_info': voices_info,
        'error_message': error_message
    }
    return render(request, 'audiospeaker_app/help.html', context)


def recognize_speech_view(request):
    """
    Отображает форму для загрузки аудио и обрабатывает запрос на распознавание.
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('audio_file')

        if not uploaded_file:
            return render(request, 'audiospeaker_app/recognize_speech.html', {
                'title': 'Распознать речь',
                'error_message': 'Пожалуйста, выберите аудиофайл для загрузки.'
            })

        rec_request = RecognitionRequest.objects.create(uploaded_audio_file=uploaded_file)

        try:
            with open(rec_request.uploaded_audio_file.path, 'rb') as audio_file:
                response = client.speech_to_text.convert(
                    file=audio_file,
                    model_id='scribe_v1'   # корректное имя модели
                )
            rec_request.recognized_text = response.text
            rec_request.status = 'COMPLETED'
            rec_request.save()

        except ApiError as e:
            rec_request.status = 'FAILED'
            rec_request.error_message = str(e)
            rec_request.save()
            print(f"Ошибка API при распознавании: {e}")
        except Exception as e:
            rec_request.status = 'FAILED'
            rec_request.error_message = f"Произошла внутренняя ошибка: {e}"
            rec_request.save()
            print(f"Неизвестная ошибка при распознавании: {e}")

        return render(request, 'audiospeaker_app/recognize_speech.html', {
            'title': 'Результат распознавания',
            'recognition_result': rec_request
        })

    return render(request, 'audiospeaker_app/recognize_speech.html', {
        'title': 'Распознать речь'
    })


@require_GET
def recognition_history_view(request):
    """
    Отображает страницу с историей всех распознанных аудио.
    """
    history_entries = RecognitionRequest.objects.all()

    context = {
        'title': 'История распознаваний',
        'history_entries': history_entries,
        'MEDIA_URL': settings.MEDIA_URL  # Явно передаем для надежности
    }
    return render(request, 'audiospeaker_app/recognition_history.html', context)
