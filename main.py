from TTS import audio_split, original_text, google_speech, new_audio
import docopt

ROOT = "androcles-shorter"

ROOT_DIR = "./{}/".format(ROOT)
TXT_PATH = ROOT_DIR + "{}_ORIGINAL.txt".format(ROOT)
NEW_TEXT_PATH = ROOT_DIR + "{}_SENTENCE.txt".format(TXT_PATH.rsplit('.', 1)[0].rsplit('/', 1)[-1])
ORIGINAL_AUDIO_PATH = ROOT_DIR + "{}.mp3".format(ROOT)
STT_PATH = ROOT_DIR + "{}_STT.txt".format(ROOT)
ORIGINAL_TXT_PATH = ROOT_DIR + "{}_ORIGINAL_SENTENCE.txt".format(ROOT)
NEW_AUDIO_PATH = ROOT_DIR + "audio/"


if __name__ == "__main__":

    # Split original text line by line
    original_text.text_load_and_save(TXT_PATH, NEW_TEXT_PATH)
    print("text is prepared")

    # Split single audio into chunks and make corresponding text
    audio_list, intervals = audio_split.split_on_silence_with_pydub(ORIGINAL_AUDIO_PATH)
    print("audio files are prepared")
    for idx in range(len(audio_list)):
        google_speech.audio_processing(audio_list[idx], intervals[idx], ROOT_DIR)

    print("Google API->done")

    # Compare sentences and make new audio files for each sentence
    new_audio.final_update(ORIGINAL_TXT_PATH, STT_PATH, ORIGINAL_AUDIO_PATH, NEW_AUDIO_PATH)

    print("Complete!")
