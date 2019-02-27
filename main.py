from TTS import audio_split, original_text, google_speech, new_audio

ROOT = "./androcles-shorter/"
TXT_PATH = ROOT + "androcles-shorter_ORIGINAL.txt"
NEW_TEXT_PATH = ROOT + "{}_SENTENCE.txt".format(TXT_PATH.rsplit('.', 1)[0].rsplit('/', 1)[-1])
ORIGINAL_AUDIO_PATH = ROOT + "pre_audio/androcles-shorter.mp3"
STT_PATH = ROOT + "androcles-shorter_STT.txt"
ORIGINAL_TXT_PATH = ROOT + "androcles-shorter_ORIGINAL_SENTENCE.txt"
AUDIO_PATH = ROOT + "androcles-shorter.mp3"
NEW_AUDIO_PATH = ROOT + "audio/"


if __name__ == "__main__":

    # Split original text line by line
    original_text.text_load_and_save(TXT_PATH, NEW_TEXT_PATH)

    # Split single audio into chunks and make corresponding text
    audio_list, intervals = audio_split.split_on_silence_with_pydub(ORIGINAL_AUDIO_PATH)
    for idx in range(len(audio_list)):
        google_speech.audio_processing(audio_list[idx], intervals[idx], ROOT)

    # Compare sentences and make new audio files for each sentence
    new_audio.final_update(ORIGINAL_TXT_PATH, STT_PATH, AUDIO_PATH)
