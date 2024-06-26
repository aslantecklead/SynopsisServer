import os
import shutil
from flask import Flask, request, jsonify
from pytube import YouTube
from flask_cors import CORS, cross_origin
import subCreator
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
CORS(app)

debug_mode = True
ready = False
last_video_code = None  # Глобальная переменная для хранения последнего video_code

@app.route('/download', methods=['GET'])
@cross_origin()
def download_audio():
    global ready, last_video_code
    try:
        if debug_mode:
            print("Начало процесса загрузки аудио")

        directory = './videos'
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print("Ошибка при удалении файла:", e)

        video_url = request.args.get('url')
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
                parsed_url = urlparse(video_url)
                last_video_code = parse_qs(parsed_url.query).get('v', [''])[0]  # Обновляем last_video_code
                subCreator.create_subtitles(last_video_code)

            return "Аудио успешно загружено"
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


def find_newest_subtitles():
    global last_video_code
    subs_directory = './subs'
    newest_subtitles = None
    newest_time = 0

    if last_video_code:  # Если есть сохранённый last_video_code, ищем файл с таким именем
        subs_file_path = os.path.join(subs_directory, f'{last_video_code}.txt')
        if os.path.exists(subs_file_path):
            return subs_file_path

    # Если нет сохранённого last_video_code или файла с таким именем, ищем самый новый файл
    for filename in os.listdir(subs_directory):
        file_path = os.path.join(subs_directory, filename)
        if os.path.isfile(file_path):
            file_time = os.path.getctime(file_path)
            if file_time > newest_time:
                newest_time = file_time
                newest_subtitles = file_path

    return newest_subtitles

@app.route('/', methods=['GET'])
@cross_origin()
def read_subs():
    try:
        subs_file_path = find_newest_subtitles()

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
            start_time, end_time = times.split(' --> ')
            subtitle = {
                "id": index,
                "startTime": start_time,
                "endTime": end_time,
                "text": text
            }
            index += 1
            subtitles.append(subtitle)
    return subtitles


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')