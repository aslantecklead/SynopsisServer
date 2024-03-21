import os
import shutil
from flask import Flask, request, jsonify
from pytube import YouTube
from flask_cors import CORS, cross_origin
import subCreator
from math import ceil
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
CORS(app)

debug_mode = True
ready = False
last_video_code = None

@app.route('/translate_to_en', methods=['POST'])
def translate_rus_text():
    data = request.json

    if 'text' not in data:
        return jsonify({'error': 'Отсутствует поле текста в запросе'}), 400

    text = data['text']

    try:
        if not text:
            return jsonify({'translated_text': ''}), 200

        translator = Translator()
        translated_text = translator.translate(text, src='ru', dest='en')
        return jsonify({'translated_text': translated_text.text}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/translate_to_ru', methods=['POST'])
def translate_eng_text():
    data = request.json

    if 'text' not in data:
        return jsonify({'error': 'Missing text field in request'}), 400

    text = data['text']

    try:
        translated_text = translate_from_english_to_russian(text)
        return jsonify({'translated_text': translated_text}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def translate_from_english_to_russian(english_text):
    try:
        if not english_text:
            return ""
        translator = Translator()
        translated_text = translator.translate(english_text, src='en', dest='ru')
        return translated_text.text
    except Exception as e:
        print("Произошла ошибка во время перевода:", e)
        raise e


@app.route('/download', methods=['GET'])
@cross_origin()
def download_audio():
    global ready, last_video_code
    try:
        if debug_mode:
            print("Начало процесса загрузки аудио")

        video_url = request.args.get('url')
        video_id = extract_video_id(video_url)
        if not video_id:
            return "Invalid video URL", 400

        subs_file_path = find_subtitles_by_video_id(video_id)
        if subs_file_path and os.path.exists(subs_file_path):
            if debug_mode:
                print("Субтитры уже существуют для данного видео. Путь к субтитрам:", subs_file_path)
            with open(subs_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                subtitles = file.read()
            subtitles_json = vtt_to_json(subtitles)
            return jsonify(subtitles_json), 200
        else:
            if debug_mode:
                print("Субтитры не найдены. Продолжение загрузки аудио...")

        directory = './videos'
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print("Ошибка при удалении файла:", e)

        yt = YouTube(video_url)
        audio_stream = yt.streams.filter(only_audio=True).first()

        if audio_stream:
            filename = audio_stream.default_filename
            new_path = os.path.join(directory, filename)

            if debug_mode:
                print("Начало загрузки аудио...")

            audio_stream.download(output_path=directory, filename=filename)

            if filename.endswith('.mp4'):
                mp3_filename = filename[:-4] + '.mp3'
                mp3_path = os.path.join(directory, mp3_filename)
                shutil.move(new_path, mp3_path)
                new_path = mp3_path

            ready = True

            if debug_mode:
                print("Аудио успешно загружено")

            if ready:
                subCreator.create_subtitles(video_id)

            subs_file_path = find_subtitles_by_video_id(video_id)
            if subs_file_path and os.path.exists(subs_file_path):
                with open(subs_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    subtitles = file.read()
                subtitles_json = vtt_to_json(subtitles)
                return jsonify(subtitles_json), 200
            else:
                return "Subtitles not found", 404
        else:
            if debug_mode:
                print("Аудиоформат не доступен")
            return "Аудиоформат не доступен", 404
    except Exception as e:
        if debug_mode:
            print("Ошибка при загрузке аудио:", e)
        return str(e), 500
    finally:
        if debug_mode:
            print("Конец процесса загрузки аудио")

def find_subtitles_by_video_id(video_id):
    subs_directory = './subs'
    subs_file_path = os.path.join(subs_directory, f'{video_id}.txt')
    if os.path.exists(subs_file_path):
        return subs_file_path
    else:
        return None

@app.route('/', methods=['GET'])
@cross_origin()
def read_subs():
    try:
        video_url = request.args.get('url')
        video_id = None
        if video_url:
            video_id = extract_video_id(video_url)
            if not video_id:
                return "Invalid video URL", 400

        subs_file_path = find_newest_subtitles() if not video_id else find_subtitles_by_video_id(video_id)

        if not subs_file_path or not os.path.exists(subs_file_path):
            return "Subtitles file not found", 404

        if os.path.getsize(subs_file_path) == 0:
            return "Subtitles file is empty", 500

        with open(subs_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            subtitles = file.read()

        subtitles_json = vtt_to_json(subtitles)

        return jsonify(subtitles_json)
    except Exception as e:
        if debug_mode:
            print("Ошибка при чтении субтитров:", e)
        return str(e), 500


def vtt_to_json(vtt_text):
    subtitles = []
    lines = vtt_text.split('\n\n')
    index = 1
    for line in lines:
        if '-->' in line:
            times, text = line.split('\n', 1)
            start_time_str, end_time_str = times.split(' --> ')
            duration = calculate_duration(start_time_str, end_time_str)

            duration = round(duration)

            start_time = start_time_str
            end_time = end_time_str
            subtitle = {
                "id": index,
                "startTime": start_time,
                "endTime": end_time,
                "duration": duration,
                "text": text
            }
            index += 1
            subtitles.append(subtitle)
    return subtitles


def find_newest_subtitles():
    subs_directory = './subs'
    newest_subtitles = None
    newest_time = 0

    for filename in os.listdir(subs_directory):
        file_path = os.path.join(subs_directory, filename)
        if os.path.isfile(file_path):
            file_time = os.path.getctime(file_path)
            if file_time > newest_time:
                newest_time = file_time
                newest_subtitles = file_path

    return newest_subtitles


def calculate_duration(start_time_str, end_time_str):
    start_parts = start_time_str.split(':')
    end_parts = end_time_str.split(':')

    start_seconds = int(start_parts[0]) * 60 + float(start_parts[1])
    end_seconds = int(end_parts[0]) * 60 + float(end_parts[1])

    duration_seconds = end_seconds - start_seconds

    return int(ceil(duration_seconds))


def time_to_seconds(time_str):
    parts = time_str.split(':')
    if '.' in parts[-1]:
        seconds, milliseconds = parts[-1].split('.')
        seconds = int(seconds)
        milliseconds = int(milliseconds)
    else:
        seconds = int(parts[-1])
        milliseconds = 0
    minutes = int(parts[-2])
    if len(parts) > 2:
        hours = int(parts[-3])
    else:
        hours = 0
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
    return total_seconds


def extract_video_id(video_url):
    try:
        parsed_url = urlparse(video_url)
        if parsed_url.netloc == 'youtu.be':
            video_id = parsed_url.path[1:]  # Извлекаем ID видео из пути URL
        elif parsed_url.netloc == 'www.youtube.com' and parsed_url.path == '/watch':
            query = parse_qs(parsed_url.query)
            video_id = query.get('v', [''])[0]  # Получаем значение параметра 'v' из запроса
        else:
            raise ValueError("Неподдерживаемый URL YouTube")

        if not video_id:
            raise ValueError("ID видео не найден в URL")

        return video_id
    except Exception as e:
        print("Ошибка при извлечении ID видео:", e)
        return None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')