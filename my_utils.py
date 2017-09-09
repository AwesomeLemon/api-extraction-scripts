# coding=utf-8
import string
from random import random
import langid

import utils


def create_dict_on_condition(sentence_list, predicate):
    word_set = set()
    for sentence in sentence_list:
        for word in sentence:
            if predicate(word):
                word_set.add(word)
    return word_set


def clean_up_sentences(list_of_sentence_pairs, api_dict):
    def clean_up_eng(sentence_eng):
        sentence_eng[:] = [word.lower().translate(str.maketrans('', '', string.punctuation)) for word in sentence_eng if
                           len(word) < 20]
        sentence_eng[:] = [word for word in sentence_eng if len(word) > 0]
        # for i, word in enumerate(words):
        #     words[i] = word.lower().translate(None, string.punctuation)

    def clean_up_api(sentence_api):
        sentence_api[:] = [call for call in sentence_api if call in api_dict]
        sentence_word_boundary = 10
        if len(sentence_api) >= sentence_word_boundary:
            words_at_ends_to_keep = 3
            start = sentence_api[:words_at_ends_to_keep]
            end = sentence_api[len(sentence_api) - words_at_ends_to_keep:]
            sentence_api[:] = start + end

    for sentence_pair in list_of_sentence_pairs:
        clean_up_eng(sentence_pair[0])
        clean_up_api(sentence_pair[1])
    list_of_sentence_pairs[:] = [(eng, api) for (eng, api) in list_of_sentence_pairs if len(eng) > 0 and len(api) > 0]
    return zip(*list_of_sentence_pairs)


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


def parse_file_to_eng_and_api(filename="data.txt", engfile="eng.txt", apifile="api.txt",
                              ifcleanup=True, ifoverwrite=False):
    english_desc = []
    api_desc = []
    unwanted_comments = [
        'Required method for Designer support - do not modify  the contents of this method with the code editor.',
        'Clean up any resources being used.',
        'The main entry point for the application.']
    with open(filename, "r", encoding='utf-8') as f:
        while True:
            line = f.readline().strip()
            if line == '':
                break
            if line.startswith("*") or line.startswith("/"):
                continue
            # if langid.classify(line)[0] != 'en':
            #     api_line = f.readline()  # we won't need it
            #     continue

            cur_eng = line.split(" ")
            line = f.readline().strip()
            cur_api = line.split(" ")

            if not (len(cur_api) == 0 or len(cur_eng) == 0):
                api_desc += [cur_api]
                english_desc += [cur_eng]

    if ifcleanup:
        api_dict = create_dict_on_condition(api_desc, lambda x: x.startswith("System.") or x.count('.') == 1)
        english_desc, api_desc = clean_up_sentences(list(zip(english_desc, api_desc)), api_dict)

    # make every pair unique
    temp = set(zip(map((lambda x: tuple(x)), english_desc), map((lambda x: tuple(x)), api_desc)))
    english_desc, api_desc = zip(*list(temp))

    # no writing to files!

    return english_desc, api_desc


def write_all_train_data_to_files(english_desc, api_desc, engfile="eng.txt", apifile="api.txt", ifoverwrite=False):
    def write_train_data_to_file(lines, filepath, file_open_modifier):
        with open(filepath, file_open_modifier, encoding='utf-8') as f:
            for sentence in lines:
                f.write(" ".join(sentence) + "\n")

    file_open_modifier = 'w' if ifoverwrite else 'a'
    write_train_data_to_file(english_desc, engfile, file_open_modifier)
    write_train_data_to_file(api_desc, apifile, file_open_modifier)


def parse_res_files_to_train_and_test(res_files=None, res_files_count=2, res_files_first=1):
    if res_files is None:
        res_files = ['/tmp/res' + str(i) + '.txt' for i in
                     range(res_files_first, res_files_count + 1)]  # ['/tmp/res1.txt', '/tmp/res2.txt']

    eng, api = parse_file_to_eng_and_api(filename=res_files[0], ifoverwrite=True)
    for res_file in res_files[1:]:
        print('parsing ' + res_file)
        eng_new, api_new = parse_file_to_eng_and_api(filename=res_file, ifoverwrite=False)
        eng += eng_new
        api += api_new

    train, dev = separate_to_train_and_dev(list(zip(eng, api)))
    eng_train, api_train = zip(*train)
    eng_dev, api_dev = zip(*dev)
    return (eng_train, eng_dev), (api_train, api_dev)


def create_vocab(sentences, vocab_size):
    vocab = {}
    for sentence in sentences:
        for w in sentence:
            if w in vocab:
                vocab[w] += 1
            else:
                vocab[w] = 1
    vocab_list = sorted(vocab, key=vocab.get, reverse=True)
    if len(vocab_list) > vocab_size:
        vocab_list = vocab_list[:vocab_size]
    return vocab_list


# def create_vocab_from_file(input_file, vocab_size):
#     print("Creating vocabulary from data %s" % (input_file))
#     with open(input_file, mode="r", encoding='utf-8') as f:
#         return create_vocab(f, vocab_size)


def write_two_vocabs(eng_vocab, api_vocab, eng_size=10000, api_size=10000, vocab_postfix=''):
    utils.write_lines_to_file('vocab' + str(eng_size) + '_test' + vocab_postfix + '.from', eng_vocab)
    utils.write_lines_to_file('vocab' + str(api_size) + '_test' + vocab_postfix + '.to', api_vocab)

if __name__ == "__main__":
    train_eng_file = 'train3.eng'
    train_api_file = 'train3.api'
    test_eng_file = 'test3.eng'
    test_api_file = 'test3.api'
    (eng_train_samples, eng_test_samples), (api_train_samples, api_test_samples) = \
        parse_res_files_to_train_and_test(res_files=['C:\\Users\\Alexander\\Google Диск\\res23.txt'],
                                          res_files_count=21, res_files_first=17)
    write_all_train_data_to_files(eng_train_samples, api_train_samples, train_eng_file, train_api_file,
                                  ifoverwrite=True)
    write_all_train_data_to_files(eng_test_samples, api_test_samples, test_eng_file, test_api_file, ifoverwrite=True)

    eng_vocab_size = 10000
    eng_vocab = create_vocab(eng_train_samples, eng_vocab_size)
    api_vocab_size = 10000
    api_vocab = create_vocab(api_train_samples, api_vocab_size)

    write_two_vocabs(eng_vocab, api_vocab, vocab_postfix='engonly')


    # test_stuff()
    # parse_file_write_to_2_files("/tmp/res1.txt","eng_dev.txt", "api_dev.txt")
    # parse_file_write_to_2_files("/tmp/res_3.txt","eng_dev.txt", "api_dev.txt")
    # create_vocab("eng_dev.txt", 'vocab' + str(10000) + '.from', 10000)
    # create_vocab("api_dev.txt", 'vocab' + str(10000) + '.to', 10000)

    # 4489200 of not unique pairs
