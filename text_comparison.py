import os
from difflib import SequenceMatcher
from pydub import AudioSegment

STT_PATH = "./androcles-shorter_STT.txt"
ORIGINAL_TXT_PATH = "./androcles-shorter_ORIGINAL_SENTENCE.txt"
AUDIO_PATH = "./androcles-shorter.mp3"
DEBUG = 0


def load_txt(path):
    with open(path, 'r') as f:
        lines = f.readlines()

    return lines


def similarity(a, b):
    a = "".join(a).lower()
    b = "".join(b).lower()
    sim = SequenceMatcher(None, a, b).ratio()

    return sim


def sentence_split(sentence):
    result = sentence.lstrip().replace("\n", "").split(" ")

    return result


def similar_word_idx(sentence, target_word, loc):
    candidate_idx = -1
    candidate_prob = -1.0
    sentence = sentence[loc:]

    for idx, word in enumerate(sentence):
        prob = similarity(sentence[idx], target_word)
        if DEBUG: print("({},{}:{:0.2f}%)".format(word, target_word, prob*100))
        if prob > candidate_prob:
            candidate_prob = prob
            candidate_idx = idx + loc
            if prob == 1.0:
                break

    if DEBUG:
        print("text:{}\ntarget:{}, candidate:{}, probability:{}\n".format
              (sentence, target_word, sentence[candidate_idx], candidate_prob))

    if candidate_prob > 0.65:         # probability threshold
        return candidate_idx
    else:
        return -1

def chunk_similarity(sentence, location, target):
    print("original chunk: {}".format(" ".join(sentence)))
    if len(sentence) >= len(target) + 1:
        chunks = {}
        chunk0 = " ".join(sentence[location:len(target)+1+location])
        chunk1 = " ".join(sentence[location + 3:len(target)+1+location+3])
        chunk2 = " ".join(sentence[location - 3:len(target)+1+location-3])
        chunks[chunk0] = similarity(chunk0, target)
        chunks[chunk1] = similarity(chunk1, target)
        chunks[chunk2] = similarity(chunk2, target)
        print(chunks)
        sim = max(chunks.values())
        for key, value in chunks.items():
            if value == sim: chunk = key.split(" ")
    else:
        chunk = sentence[:]
        sim = similarity(chunk, target)
    print("chunk to compare:{}, sim:{}".format(chunk, sim))

    return sim, chunk


def update(text):
    idx_list = [[-1, -1]]
    unknown = []
    stt_text = load_txt(STT_PATH)  # [idx, start, end, sentence]

    loc_list = []
    target_idx = 1
    sent_idx = 0
    chunk_loc= 0
    loc = 0                                     # starting point to analyze
    on = 0

    while target_idx < len(stt_text) and sent_idx < len(text):
        sentence = sentence_split(text[sent_idx].split(",", 1)[1])              # word list in a sentence to compare
        target = sentence_split(stt_text[target_idx].split(',')[3])             # word list in a target to compare
        print("original sentence number:{}, length:{}\ntarget to analyze:{}".format(sent_idx, len(sentence), target))
        start = -1
        end = -1
        chunk_loc += len(target)
        print("start location: {}".format(loc))
        sim, chunk = chunk_similarity(sentence, loc, target)

        if sim > 0.6:
            print("chunk is simlar!")
            for index, word in enumerate(target):
                idx = similar_word_idx(sentence, word, loc)
                print("word: {}, index: {}".format(word, idx))
                if idx == 0 and on == 0:
                    start = stt_text[target_idx].split(",")[1]
                    loc_list = []
                    loc += 1
                    on = 1
                elif index == len(target)-1 and idx == len(sentence)-1:
                    print("finally, index: {}".format(idx))
                    end = stt_text[target_idx].split(",")[2]
                    # Go to next sentence and Reset location
                    sent_idx += 1
                    chunk_loc = 0
                    on = 0
                    loc = 0
                    loc_list = []
                    idx_list.append([-1, -1])
                    print("sentence index: {}".format(sent_idx))
                    break
                elif idx == -1:
                    continue
                else:
                    print("chunk location: {}".format(chunk_loc))
                    if idx <= chunk_loc: loc_list.append(idx+1)
                    loc = max(loc_list) + 1
                if index == len(target)-1 and idx != -1:                    # last item in target matches exactly!
                    loc = idx + 1

        else:
            unknown.append(" ".join(target))
            loc += len(target)

        if start != -1:
            idx_list[sent_idx][0] = start
        if end != -1:
            idx_list[sent_idx-1][1] = end
        print(idx_list)
        target_idx += 1
        print("target index: {}, location: {}\n".format(target_idx, loc))
        chunk_loc = loc
        if loc >= len(sentence):
            sent_idx += 1
            loc = 0
            chunk_loc = 0
            on = 0
            idx_list.append([-1, -1])

    print(idx_list, "\n", unknown)

    return idx_list, unknown


def elaboration(intervals):
    padding = 500
    # String to integer
    for idx in range(len(intervals)):
        intervals[idx][0] = int(intervals[idx][0])
        intervals[idx][1] = int(intervals[idx][1])

    # elaborate unknown intervals
    for idx, [start, end] in enumerate(intervals):
        if idx < len(intervals) - 1:
            if end == -1 and intervals[idx+1][0] != -1:
                intervals[idx][1] = intervals[idx+1][0] - padding
            if idx > 0 and start == -1 and intervals[idx-1][1] != -1:
                intervals[idx][0] = intervals[idx-1][1] + padding

    return intervals


def audio_update(audio_path, intervals, out_ext="wav"):
    padding = 50
    audio = AudioSegment.from_file(audio_path)
    filename = os.path.basename(audio_path).split('.', 1)[0]

    for idx, (start_idx, end_idx) in enumerate(intervals[:]):
        if start_idx != -1 and end_idx != -1:
            target_audio_path = "./audio/{}.{:04d}.{}".format(filename, idx, out_ext)
            segment = audio[start_idx-padding:end_idx+padding]
            segment.export(target_audio_path, out_ext)


if __name__ == "__main__":
    txt = load_txt(ORIGINAL_TXT_PATH)
    stt_txt = load_txt(STT_PATH)                    # [idx, start, end, sentence]
    intervals, unknowns = update(txt, stt_txt)
    intervals = elaboration(intervals)
    print(intervals)
    audio_update(AUDIO_PATH, intervals)
