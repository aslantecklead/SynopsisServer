import os
import shutil
import assemblyai as aai

subsReady = False


def create_subtitles(audio_url):
    global subsReady
    aai.settings.api_key = "5f4d8d4e034a4870b1b180ff4f804f52"

    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_url)
        subs = transcript.export_subtitles_vtt(chars_per_caption=200)

        subs_directory = os.path.join('.', 'subs')
        if not os.path.exists(subs_directory):
            os.makedirs(subs_directory)

        subs_file_path = os.path.join(subs_directory, 'subs.txt')
        with open(subs_file_path, "w") as f:
            f.write(subs)
        print(subs)
        subsReady = True
        print("Субтитры готовы")
    except Exception as e:
        print("Ошибка при создании субтитров:", e)


def delete_old_subs():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    subs_directory = os.path.join(current_directory, '..', 'subs')

    for file_name in os.listdir(subs_directory):
        file_path = os.path.join(subs_directory, file_name)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print("Ошибка при удалении файла:", e)