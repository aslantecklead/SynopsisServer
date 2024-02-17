import os
import shutil
from flask import Flask, request, send_file
from pytube import YouTube
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)

debug_mode = True
ready = False

@app.route('/download', methods=['GET'])
@cross_origin()
def download_audio():
    global ready
    try:
        if debug_mode:
            print("Начало процесса загрузки аудио")

        # Удаление файлов из папки videos
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

            return send_file(new_path, as_attachment=True)
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

if __name__ == '__main__':
    app.run(debug=True)
