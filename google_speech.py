import io
import os

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types


def call_google(audio):
    client = speech.SpeechClient()

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code='en-US')

    response = client.recognize(config, audio)
    if len(response.results) < 1:
        return None
    else:
        trans = response.results[0].alternatives[0].transcript

    return trans


def audio_processing(path, intervals, root):
    name = os.path.splitext(path)[0].rsplit('.', 1)[0].rsplit('/')[-1]
    line_number = os.path.splitext(path)[0].rsplit('.', 1)[1]

    txt_path = name + "_STT.txt"

    # Loads the audio into memory
    with io.open(path, 'rb') as audio_file:
        audio = types.RecognitionAudio(content=audio_file.read())
        # audio_duration = AudioSegment.from_file(path).duration_seconds

    trans = call_google(audio)
    if not trans is None:
        data = "{},{},{},{}\n".format(line_number, intervals[0], intervals[1], trans)

        if os.path.exists(root + txt_path):
            with open(root + txt_path, 'a') as f:
                f.write(data)
        else:
            with open(root + txt_path, 'w') as f:
                f.write(data)
    else:
        pass
