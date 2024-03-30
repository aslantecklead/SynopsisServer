import os
import shutil
from flask import Flask, request, jsonify, session
from pytube import YouTube
from flask_cors import CORS, cross_origin
from googletrans import Translator
from urllib.parse import urlparse, parse_qs
import sys

app = Flask(__name__)
app.secret_key = 'your_secret_key'
CORS(app)

ready = False
last_video_code = None

debug_mode = True


@app.route('/generate_error', methods=['GET'])
def generate_error():
    1 / 0


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
        print("Error occurred during translation:", e)
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
        print("Error occurred during translation:", e)
        return jsonify({'error': str(e)}), 500


def translate_from_english_to_russian(english_text):
    try:
        if not english_text:
            return ""
        translator = Translator()
        translated_text = translator.translate(english_text, src='en', dest='ru')
        return translated_text.text
    except Exception as e:
        print("Error occurred during translation:", e)
        raise e


@app.route('/download', methods=['GET'])
@cross_origin()
def download_audio():
    try:
        if debug_mode:
            print("Beginning audio download process")

        video_url = request.args.get('url')
        video_id = extract_video_id(video_url)
        if not video_id:
            return "Invalid video URL", 400

        session['last_video_id'] = video_id

        subs_file_path = find_subtitles_by_video_id(video_id)
        if subs_file_path and os.path.exists(subs_file_path):
            if debug_mode:
                print("Subtitles already exist for this video. Subtitles path: %s", subs_file_path)
            with open(subs_file_path, 'r', encoding='utf-8', errors='ignore') as file:
                subtitles = file.read()
            subtitles_json = vtt_to_json(subtitles)
            return jsonify(subtitles_json), 200
        else:
            if debug_mode:
                print("Subtitles not found. Continuing audio download...")

        directory = './videos'
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print("Error deleting file: %s", e)

        yt = YouTube(video_url)
        audio_stream = yt.streams.filter(only_audio=True).first()

        if audio_stream:
            filename = audio_stream.default_filename
            new_path = os.path.join(directory, filename)

            if debug_mode:
                print("Starting audio download...")

            audio_stream.download(output_path=directory, filename=filename)

            if filename.endswith('.mp4'):
                mp3_filename = filename[:-4] + '.mp3'
                mp3_path = os.path.join(directory, mp3_filename)
                shutil.move(new_path, mp3_path)
                new_path = mp3_path

            ready = True

            if debug_mode:
                print("Audio downloaded successfully")

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
                print("Audio format not available")
            return "Audio format not available", 404
    except Exception as e:
        print("Error occurred during audio download:", e)
        return str(e), 500
    finally:
        if debug_mode:
            print("End of audio download process")


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
        video_id = session.get('last_video_id')

        if not video_id:
            return "No video selected", 404

        subs_file_path = find_subtitles_by_video_id(video_id)
        if not subs_file_path or not os.path.exists(subs_file_path):
            return "Subtitles file not found", 404
        if os.path.getsize(subs_file_path) == 0:
            return "Subtitles file is empty", 500
        with open(subs_file_path, 'r', encoding='utf-8', errors='ignore') as file:
            subtitles = file.read()
        subtitles_json = vtt_to_json(subtitles)
        return jsonify(subtitles_json)

    except Exception as e:
        print("Error occurred while reading subtitles:", e)
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
            video_id = parsed_url.path[1:]
        elif parsed_url.netloc == 'www.youtube.com' and parsed_url.path == '/watch':
            query = parse_qs(parsed_url.query)
            video_id = query.get('v', [''])[0]
        else:
            raise ValueError("Неподдерживаемый URL YouTube")

        if not video_id:
            raise ValueError("ID видео не найден в URL")

        return video_id
    except Exception as e:
        print("Ошибка при извлечении ID видео:", e)
        return None


if __name__ == '__main__':
    app.run(debug=False, host="0.0.0.0", host=5000)
