# coding=utf-8
import string
import operator
from random import random

from tensorflow.python.platform import gfile

import tensorflow as tf
import langid

def clean_up_sentences(list_of_sentence_pairs):
    def clean_up(sentence_eng):
        sentence_eng[:] = [word.lower().translate(str.maketrans('','',string.punctuation)) for word in sentence_eng if len(word) < 20]
        sentence_eng[:] = [word for word in sentence_eng if len(word) > 0]
        # for i, word in enumerate(words):
        #     words[i] = word.lower().translate(None, string.punctuation)

    for sentence_pair in list_of_sentence_pairs:
        clean_up(sentence_pair[0])
    # list_of_sentences = [clean_up(sentence) for sentence in list_of_sentences]
    list_of_sentence_pairs[:] = [(eng, api) for (eng, api) in list_of_sentence_pairs if len(eng) > 0]
    # for i, sentence in enumerate(list_of_sentences):
    #     clean_up(sentence)

def separate_to_train_and_dev(eng_api_list):
    total = len(eng_api_list)
    prob_boundary = 10100.0 / float(total)
    dev = []
    train = []
    for pair in eng_api_list:
        if random() <= prob_boundary:
            dev.append(pair)
        else:
            train.append(pair)
    return train, dev

def read_from_file(filename="data.txt", ifcleanup=True):
    english_desc = []
    api_desc = []
    with open(filename, "r") as f:
        while True:
            line = f.readline().strip()
            if line == '':
                break
            if line.startswith("*") or line.startswith("/"):
                continue
            cur_eng = line.split(" ")
            line = f.readline().strip()
            cur_api = line.split(" ")

            if not (len(cur_api) == 0 or len(cur_eng) == 0):
                api_desc += [cur_api]
                english_desc += [cur_eng]

    if ifcleanup:
        clean_up_sentences(english_desc)
    # clean_up_list_of_lists(api_desc)
    return english_desc, api_desc


def construct_good_set(data, top=300, skip=10):
    word_cnt = {}
    for sentence in data:
        for word in sentence:
            if word_cnt.__contains__(word):
                word_cnt[word] += 1
            else:
                word_cnt[word] = 1
    top_eng_words = sorted(word_cnt.items(), key=operator.itemgetter(1), reverse=True)
    return set([key for (key, value) in top_eng_words][skip:top + skip - 1])


def filter_sentences(data, good_set):
    words_to_nums = {}
    cur = 1
    for i, sentence in enumerate(data):
        data[i] = filter(lambda x: x in good_set, sentence)
        for j, word in enumerate(data[i]):
            if not words_to_nums.__contains__(word):
                words_to_nums[word] = cur
                cur += 1
            data[i][j] = words_to_nums[word]
            # data[i] = filter(lambda x: x in good_set, sentence)
            # data[i] = map(lambda x: 1 if words_to_nums.__contains__(x) else 2, sentence)


def get_data(eng_top=10000, eng_skip=5, api_top=10000, api_skip=0, fromfile=False):
    if fromfile:
        return read_from_file("clean.txt", False)
    else:
        (eng, api) = read_from_file()
        eng_set = construct_good_set(eng, top=eng_top, skip=eng_skip)
        api_set = construct_good_set(api, top=api_top, skip=api_skip)
        filter_sentences(eng, eng_set)
        filter_sentences(api, api_set)
        deleted = 0
        for i, (x, y) in enumerate(zip(eng, api)):
            if (len(x) == 0 or len(y) == 0):
                eng.__delitem__(i - deleted)
                api.__delitem__(i - deleted)
                deleted += 1
        return eng, api


def refactored_data_to_file(eng_top=10000, eng_skip=5, api_top=10000, api_skip=0):
    (eng, api) = get_data(eng_top, eng_skip, api_top, api_skip, False)
    filename = "clean.txt"
    with open(filename, 'w') as f:
        for words_e, words_a in zip(eng, api):
            if len(words_a) == 0:
                continue
            for word in words_e:
                f.write(str(word) + " ")
            f.write("\n")
            for word in words_a:
                f.write(str(word) + " ")
            f.write("\n")


# for Tensorflow:

def parse_file_write_to_2_files(filename="data.txt", engfile="eng.txt", apifile="api.txt",
                                ifcleanup=True, ifoverwrite=False):
    english_desc = []
    api_desc = []
    unwanted_comments = [
        'Required method for Designer support - do not modify  the contents of this method with the code editor.',
        'Clean up any resources being used.',
        'The main entry point for the application.']
    with open(filename, "r") as f:
        while True:
            line = f.readline().strip()
            if line == '':
                break
            if line.startswith("*") or line.startswith("/"):
                continue
            if langid.classify(line)[0] != 'en':
                api_line = f.readline() # we won't need it
                continue

            cur_eng = line.split(" ")
            line = f.readline().strip()
            cur_api = line.split(" ")

            if not (len(cur_api) == 0 or len(cur_eng) == 0):
                api_desc += [cur_api]
                english_desc += [cur_eng]

    if ifcleanup:
        clean_up_sentences(list(zip(english_desc, api_desc)))

    #make every pair unique
    temp = set(zip(map((lambda x:tuple(x)), english_desc), map((lambda x:tuple(x)), api_desc)))
    english_desc, api_desc = zip(*list(temp))

    #no writing to files!

    # clean_up_list_of_lists(api_desc)
    return english_desc, api_desc


def write_all_train_data_to_files(english_desc, api_desc, engfile="eng.txt", apifile="api.txt", ifoverwrite=False):
    def write_train_data_to_file(lines, filepath, file_open_modifier):
        with open(filepath, file_open_modifier) as f:
            for sentence in lines:
                f.write(" ".join(sentence) + "\n")
    file_open_modifier = 'w' if ifoverwrite else 'a'
    write_train_data_to_file(english_desc, engfile, file_open_modifier)
    write_train_data_to_file(api_desc, apifile, file_open_modifier)


def parse_res_files_to_two_files(engfile="eng.txt", apifile="api.txt",
                                 eng_dev_file="eng_dev.txt", api_dev_file="api_dev.txt",
                                 res_files=None, res_files_count=2, res_files_first=1):
    if res_files is None:
        res_files = ['/tmp/res' + str(i) + '.txt' for i in range(res_files_first, res_files_count + 1)]#['/tmp/res1.txt', '/tmp/res2.txt']

    eng, api = parse_file_write_to_2_files(filename=res_files[0], ifoverwrite=True)
    # train, dev = separate_to_train_and_dev(list(zip(eng, api)))
    # eng_train, api_train = zip(*train)
    # eng_dev, api_dev = zip(*dev)
    # write_all_train_data_to_files(eng_train, api_train, engfile, apifile, ifoverwrite=True)
    # write_all_train_data_to_files(eng_dev, api_dev, eng_dev_file, api_dev_file, ifoverwrite=True)
    for res_file in res_files[1:]:
        print('parsing ' + res_file)
        eng_new, api_new = parse_file_write_to_2_files(filename=res_file, ifoverwrite=False)
        eng += eng_new
        api += api_new

    train, dev = separate_to_train_and_dev(list(zip(eng, api)))
    eng_train, api_train = zip(*train)
    eng_dev, api_dev = zip(*dev)
    write_all_train_data_to_files(eng_train, api_train, engfile, apifile, ifoverwrite=True)
    write_all_train_data_to_files(eng_dev, api_dev, eng_dev_file, api_dev_file, ifoverwrite=True)


def create_vocab(input_file, vocab_file, vocab_size):
    # if gfile.Exists(vocab_file): return

    print("Creating vocabulary %s from data %s" % (vocab_file, input_file))
    vocab = {}
    with gfile.GFile(input_file, mode="r") as f:
        counter = 0
        for line in f:
            counter += 1
            if counter % 100000 == 0:
                print("  processing line %d" % counter)
            # line = tf.compat.as_bytes(line)
            tokens = line.strip().split(" ")
            for w in tokens:
                if w in vocab:
                    vocab[w] += 1
                else:
                    vocab[w] = 1
        vocab_list = sorted(vocab, key=vocab.get, reverse=True)
        if len(vocab_list) > vocab_size:
            vocab_list = vocab_list[:vocab_size]
        with gfile.GFile(vocab_file, mode="w") as vocab_file:
            for w in vocab_list:
                vocab_file.write(w + "\n")

# def test_stuff():
#     english_desc = ["ab", "cd", "ab", "xy"]
#     api_desc = ["da", "db", "da", "aa"]
#     english_desc, api_desc = zip(*list(set(zip(english_desc, api_desc))))
#     print english_desc
#     print api_desc


def create_two_vocabs(eng='eng.txt', api='api.txt', eng_size=10000, api_size=10000, vocab_postfix = ''):
    # create_vocab(eng, 'vocab{0}_test.from'.format(str(eng_size)), eng_size)
    # create_vocab(api, 'vocab{0}_test.to'.format(str(api_size)), api_size)
    create_vocab(eng, 'vocab' + str(eng_size) + '_test' + vocab_postfix + '.from', eng_size)
    create_vocab(api, 'vocab' + str(api_size) + '_test' + vocab_postfix + '.to', api_size)
if __name__ == "__main__":
    parse_res_files_to_two_files('train3.eng', 'train3.api', 'test3.eng', 'test3.api', res_files_count=21, res_files_first=17)
    # create_two_vocabs('train2.eng', 'train2.api', vocab_postfix='engonly')

    # test_stuff()
    # parse_file_write_to_2_files("/tmp/res1.txt","eng_dev.txt", "api_dev.txt")
    # parse_file_write_to_2_files("/tmp/res_3.txt","eng_dev.txt", "api_dev.txt")
    # create_vocab("eng_dev.txt", 'vocab' + str(10000) + '.from', 10000)
    # create_vocab("api_dev.txt", 'vocab' + str(10000) + '.to', 10000)

#4489200 of not unique pairs