import os
import shutil
import assemblyai as aai

subsReady = False


def create_subtitles(video_code):
    global subsReady
    print("Starting subtitle creation process...")

    aai.settings.api_key = "0bfaaf47a21c4ab0a1588fe25c7813e7"

    current_directory = os.path.dirname(os.path.abspath(__file__))
    subs_directory = os.path.join(current_directory, '..', 'subs')
    subs_file_path = os.path.join(subs_directory, f'{video_code}.txt')

    if os.path.exists(subs_file_path):
        print("Subtitles already exist for this video.")
        subsReady = True
        return

    video_directory = os.path.join(current_directory, '..', 'videos')

    video_file_path = None
    for filename in os.listdir(video_directory):
        if filename.endswith('.mp3'):
            video_file_path = os.path.join(video_directory, filename)
            break

    if video_file_path:
        print("Transcribing audio to subtitles...")

        try:
            transcriber = aai.Transcriber().transcribe(video_file_path)
            subs = transcriber.export_subtitles_vtt(chars_per_caption=150)
            print("1")

            if not os.path.exists(subs_directory):
                os.makedirs(subs_directory)
            print("2")

            with open(subs_file_path, "w") as f:
                f.write(subs)
                print("3")

            subsReady = True
            print("Subtitles are ready")
        except Exception as e:
            print("Error during transcription:", e)
    else:
        print("No MP3 files found in the 'videos' folder")