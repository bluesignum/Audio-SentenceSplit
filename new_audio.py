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


def blank_intervals(txt):
    intervals = []

    for i in range(len(txt)):
        intervals.append([-1, -1])

    return intervals


def sentence_split(sentence):
    result = sentence.lstrip().replace("\n", "").split(" ")

    return result


def similar_word_idx(sentence, target_word, loc, end):
    candidate_idx = -1
    candidate_prob = -1.0
    new_sentence = sentence[loc:loc+end+1]
    for idx, word in enumerate(new_sentence):
        prob = similarity(new_sentence[idx], target_word)
        if DEBUG : print("({},{}:{:0.2f}%)".format(word, target_word, prob*100))
        if prob > candidate_prob:
            candidate_prob = prob
            candidate_idx = idx + loc
            if prob == 1.0:
                break

    print("chunk word:{}, candidate:{}, probability:{}\n".format
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

    print("sentence: {}, case: {}".format(sentence, case))
    for i in range(case):
        part = " ".join(sentence[i:i+len(chunk)+1])                 # 탐색구간 한칸 더 크게
        sims[i] = similarity(part, chunk)

    high_sim = max(sims.values()) if len(sims.values()) > 0 else 0

    for key, value in sims.items():
        if value == high_sim:
            start = key
            part = sentence[key:key+len(chunk)+1]

    print("chunk: {}\nsimilar part: {}\nkey: {}, similarity: {}".format(chunk, part, start, high_sim))

    return start, high_sim


def update(text, stt_text, intervals):
    unknowns = []
    findings = {}

    breaker = False
    sent_idx = 0

    # Analyze sentence in order
    while sent_idx < len(text):
        sentence = sentence_split(text[sent_idx].split(",", 1)[1])  # word list in a sentence to compare
        loc, on = 0, 0
        l = []

        print("original sentence number:{}, length:{}".format(sent_idx, len(sentence)))
        for i, data in enumerate(stt_text):                         # Start to compare chunk to sentence in order
            stt_data = data.split(',')
            chunk = sentence_split(stt_data[3])
            key, sim = find_similar_part(sentence, chunk)

            if sim >= 0.6:                                          # 비슷한 덩어리를 문장에서 찾았을 때
                print("chunk is similar!")
                for a, word in enumerate(chunk):
                    idx = similar_word_idx(sentence, word, key, len(chunk))
                    if idx == 0 and on == 0:
                        intervals[sent_idx][0] = stt_data[1]        # update start
                        on = 1
                        loc += 1
                    elif idx == len(sentence)-1:
                        intervals[sent_idx][1] = stt_data[2]        # update end
                        print("intervals: {}".format(intervals))
                        sent_idx += 1
                        breaker = True
                        break
                    elif idx != -1:                                 # neither start nor end
                        findings[idx] = a

                stt_text[i] = ",,,"
                print(stt_text)
                if breaker: break

                l = [n for n in findings.keys() if 0 < n < key+len(chunk)]
                print("location candidates: {}".format(l))
                if len(l) > 0 : loc = max(l) + len(chunk) - findings[max(l)]
                print("final location: {}".format(loc))

            else:                                                   # 못찾았을 때
                unknowns.append(",".join(stt_data))
                # for x, word in enumerate(chunk):
                #     idx = similar_word_idx(sentence, word, loc, len(chunk))
                #     if idx != -1 and idx != 0 and len(word) >= 4 and \
                #         idx + (len(chunk) - x - 1) >= len(sentence):x
                #             sent_idx +=1
                #             break
                loc += len(chunk)
                print("current location: {}\n".format(loc))

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
    stt_txt = load_txt(STT_PATH)
    new_intervals = blank_intervals(txt)
    intervals, unknowns, stt_txt = update(txt, stt_txt, new_intervals)
    print("#################\nStt_Text_Remaining: {}\n".format(stt_txt))
    #intervals, unknowns = update(txt, list(set(unknowns)), intervals)
    # intervals = elaboration(intervals)
    print("intervals:{}\nunknowns:{}".format(intervals, set(unknowns)))
