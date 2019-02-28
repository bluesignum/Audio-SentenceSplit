import os
import re
from difflib import SequenceMatcher
from pydub import AudioSegment

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


def blank_intervals(txt):
    intervals = []

    for i in range(len(txt)):
        intervals.append([-1, -1])

    return intervals


def text_processing(txt):
    txt = re.sub('[^A-Za-z0-9]+', '', txt)

    return txt


def sentence_split(sentence):
    result = sentence.lstrip().replace("\n", "").split(" ")

    return result


def similar_word_idx(sentence, target_word, loc, end):
    candidate_idx = -1
    candidate_prob = -1.0
    new_sentence = sentence[loc:loc+end+1]
    for idx, word in enumerate(new_sentence):
        prob = similarity(text_processing(new_sentence[idx]), target_word)
        if prob > candidate_prob:
            candidate_prob = prob
            candidate_idx = idx + loc
            if prob == 1.0:
                break

    if DEBUG: print("chunk word:{}, candidate:{}, probability:{}\n".format
                    (target_word, sentence[candidate_idx], candidate_prob))

    if candidate_prob > 0.65:                                       # probability threshold
        return candidate_idx
    else:
        return -1


def find_similar_part(sentence, chunk):
    case = len(sentence) - len(chunk) + 1 if len(chunk) <= len(sentence) else 1
    sims = {}
    start = 0
    part = None

    if DEBUG: print("sentence: {}, case: {}".format(sentence, case))
    for i in range(case):
        part = " ".join(sentence[i:i+len(chunk)+1])                 # 탐색구간 한칸 더 크게
        sims[i] = similarity(part, chunk)

    high_sim = max(sims.values()) if len(sims.values()) > 0 else 0

    for key, value in sims.items():
        if value == high_sim:
            start = key
            part = sentence[key:key+len(chunk)+1]

    if DEBUG: print("chunk: {}\nsimilar part: {}\nkey: {}, similarity: {}".format(chunk, part, start, high_sim))

    return start, high_sim


def update(text, stt_text, intervals):
    unknowns = []
    findings = {}

    breaker = False
    sent_idx = 0
    init = 0
    point = 0

    # Analyze sentence in order
    while sent_idx < len(text):
        sentence = sentence_split(text[sent_idx].split(",", 1)[1])  # word list in a sentence to compare
        loc, on = 0, 0
        l = []
        init += point
        point = 0

        if DEBUG: print("original sentence number:{}, length:{}".format(sent_idx, len(sentence)))
        for i in range(len(stt_text)):                                   # Start to compare chunk to sentence in order
            stt_data = stt_text[i+init].split(',')
            chunk = sentence_split(stt_data[3])
            key, sim = find_similar_part(sentence, chunk)

            if sim >= 0.6:                                          # Similar chunk is in the sentence
                point += 1
                if DEBUG: print("chunk is similar!")
                for a, word in enumerate(chunk):
                    idx = similar_word_idx(sentence, word, key, len(chunk))
                    if idx == 0 and on == 0:
                        intervals[sent_idx][0] = stt_data[1]        # update start
                        on = 1
                        loc = 1
                    elif idx == len(sentence)-1:
                        intervals[sent_idx][1] = stt_data[2]        # update end
                        sent_idx += 1
                        breaker = True
                        break
                    elif idx != -1:                                 # neither start nor end
                        findings[idx] = a

                if breaker: break

                l = [n for n in findings.keys() if 0 < n < key+len(chunk)]
                if len(l) > 0 : loc = max(l) + len(chunk) - findings[max(l)]
                if DEBUG: print("final location: {}".format(loc))

            else:                                                   # NOT FOUND
                unknowns.append(",".join(stt_data))
                # for x, word in enumerate(chunk):
                #     idx = similar_word_idx(sentence, word, loc, len(chunk))
                #     if idx != -1 and idx != 0 and len(word) >= 4 and \
                #         idx + (len(chunk) - x - 1) >= len(sentence):x
                #             sent_idx +=1
                #             break
                loc += len(chunk)
                if DEBUG: print("current location: {}\n".format(loc))

            if loc >= len(sentence):
                sent_idx += 1
                break

    return intervals, unknowns, stt_text


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


def audio_update(audio_path, new_audio_path, intervals, out_ext="wav"):
    padding = 100
    audio = AudioSegment.from_file(audio_path)
    filename = os.path.basename(audio_path).split('.', 1)[0]
    success = 0

    for idx, (start_idx, end_idx) in enumerate(intervals):
        if start_idx != -1 and end_idx != -1:
            success += 1
            target_audio_path = new_audio_path + "{}.{:>4d}.{}".format(filename, idx, out_ext)
            segment = audio[start_idx-padding:end_idx+padding]
            segment.export(target_audio_path, out_ext)

    print("Success: {} files! (out of {})".format(success, len(intervals)))


def final_update(original_txt_path, stt_path, audio_path, new_audio_path):
    txt = load_txt(original_txt_path)
    stt_txt = load_txt(stt_path)
    new_intervals = blank_intervals(txt)

    intervals, unknowns, stt_txt = update(txt, stt_txt, new_intervals)
    if DEBUG: print("intervals:{}\nunknowns:{}".format(intervals, set(unknowns)))

    intervals = elaboration(intervals)
    if DEBUG: print("elaborated intervals: {}".format(intervals))

    audio_update(audio_path, new_audio_path, intervals)


# if __name__ == "__main__":
#     STT_PATH = "./androcles-shorter_STT.txt"
#     ORIGINAL_TXT_PATH = "./androcles-shorter_ORIGINAL_SENTENCE.txt"
#     AUDIO_PATH = "./androcles-shorter.mp3"
#     NEW_AUDIO_PATH = "./audio/"
#
#     final_update(ORIGINAL_TXT_PATH, STT_PATH, AUDIO_PATH, NEW_AUDIO_PATH)
