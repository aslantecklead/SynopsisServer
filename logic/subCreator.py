import os
import shutil
import assemblyai as aai

subsReady = False


def create_subtitles(video_code):
    global subsReady
    aai.settings.api_key = "5f4d8d4e034a4870b1b180ff4f804f52"

    current_directory = os.path.dirname(os.path.abspath(__file__))
    subs_directory = os.path.join(current_directory, '..', 'subs')
    subs_file_path = os.path.join(subs_directory, f'{video_code}.txt')

    if os.path.exists(subs_file_path):
        print("Субтитры уже существуют для данного видео.")
        subsReady = True
        return

    video_directory = os.path.join(current_directory, '..', 'videos')

    video_file_path = None
    for filename in os.listdir(video_directory):
        if filename.endswith('.mp3'):
            video_file_path = os.path.join(video_directory, filename)
            break

    if video_file_path:
        transcriber = aai.Transcriber().transcribe(video_file_path)
        subs = transcriber.export_subtitles_vtt(chars_per_caption=150)

        if not os.path.exists(subs_directory):
            os.makedirs(subs_directory)

        with open(subs_file_path, "w") as f:
            f.write(subs)
        subsReady = True
        print("Субтитры готовы")
    else:
        print("Нет файлов формата MP3 в папке videos")
