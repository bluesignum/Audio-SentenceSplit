import re

DEBUG = 0


def text_processing(txt):
    txt = re.sub('[^A-Za-z0-9]+', '', txt)

    return txt


# Return whether the item in list is including ends such as punctuations and question marks.
def is_including_ends(sentence):
    if "." in sentence or "?" in sentence or "!" in sentence:
        return True
    else:
        return False


# Get whole lines in text and split it into words list
def split_into_words(txt):
    text = []

    for line in txt:
        for sentence in line.replace("\n", " ").split(" "):
            if len(sentence) > 0:
                text.append(sentence.lstrip())

    return text


# Change words list to sentence list using "is including ends" function (from Start ~ word including ends)
def create_sentence(txt):
    start_idx = 0
    sentences = []

    for idx in range(len(txt)):
        if is_including_ends(txt[idx]):
            sentences.append(" ".join(txt[start_idx:idx + 1]))
            start_idx = idx + 1

    return sentences


def text_load_and_save(path, new_text_path):
    with open(path, 'r') as f:
        txt = f.readlines()

    txt = split_into_words(txt)
    txt = create_sentence(txt)

    with open(new_text_path, 'w') as f:
        for idx in range(len(txt)):
            f.write("{0:04d}, ".format(idx) + txt[idx] + "\n")

    if DEBUG:
        print("Complete!")
