import os
import shutil
from flask import Flask, request, jsonify
from pytube import YouTube
from flask_cors import CORS, cross_origin
import subCreator
import re

app = Flask(__name__)
CORS(app)

debug_mode = True
ready = False

@app.route('/download', methods=['GET'])
@cross_origin()
def download_audio():
    global ready
    try:
        subCreator.delete_old_subs()
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
        subCreator.create_subtitles(video_url)

        return "Аудио успешно загружено и субтитры созданы"
    except Exception as e:
        if debug_mode:
            print("Ошибка при загрузке аудио и создании субтитров:", e)
        return str(e), 500


@app.route('/', methods=['GET'])
@cross_origin()
def read_subs():
    try:
        subs_file_path = './subs/subs.txt'

        if not os.path.exists(subs_file_path):
            return "Файл субтитров не найден", 404

        if os.path.getsize(subs_file_path) == 0:
            return "Файл субтитров пуст", 500

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
    for line in lines:
        if '-->' in line:
            times, text = line.split('\n', 1)
            start_time, end_time = times.split(' --> ')
            subtitles.append({
                "startTime": start_time,
                "endTime": end_time,
                "text": text
            })
    return subtitles

if __name__ == '__main__':
    app.run(debug=True)
