# coding=utf-8
import string
from random import random
import langid

import remove_empty_lines
import utils
from database import parse_database_to_eng_and_api


def create_dict_on_condition(sentence_list, predicate):
    word_set = set()
    for sentence in sentence_list:
        for word in sentence:
            if predicate(word):
                word_set.add(word)
    return word_set


def clean_up_sentences(list_of_sentence_pairs, api_dict=None, if_shorten=False, if_remove_repetitions=False):
    def clean_up_eng(sentence_eng):
        sentence_eng[:] = [word.lower().translate(str.maketrans('', '', string.punctuation)) for word in sentence_eng if
                           len(word) < 20]
        sentence_eng[:] = [word for word in sentence_eng if len(word) > 0]
        # for i, word in enumerate(words):
        #     words[i] = word.lower().translate(None, string.punctuation)

    def clean_api_by_dict(sentence_api):
        sentence_api[:] = [call for call in sentence_api if call in api_dict]

    def clean_api_shorten(sentence_api):
        sentence_word_boundary = 10
        if len(sentence_api) >= sentence_word_boundary:
            words_at_ends_to_keep = 3
            start = sentence_api[:words_at_ends_to_keep]
            end = sentence_api[len(sentence_api) - words_at_ends_to_keep:]
            sentence_api[:] = start + end

    def clean_api_consecutive_repetitions(sentence_api):
        prev = None
        res = []
        for word in sentence_api:
            if word != prev:
                res.append(word)
            prev = word
        sentence_api[:] = res

    for sentence_pair in list_of_sentence_pairs:
        clean_up_eng(sentence_pair[0])
        if api_dict is not None:
            clean_api_by_dict(sentence_pair[1])
        if if_shorten:
            clean_api_shorten(sentence_pair[1])
        if if_remove_repetitions:
            clean_api_consecutive_repetitions(sentence_pair[1])
    list_of_sentence_pairs[:] = [(eng, api) for (eng, api) in list_of_sentence_pairs if len(eng) > 0 and len(api) > 0]
    # return zip(*list_of_sentence_pairs)
    return list_of_sentence_pairs


def separate_to_train_and_dev(eng_api_list):
    total = len(eng_api_list)
    test_size = 10000.0
    prob_boundary = test_size / float(total)
    dev = []
    train = []
    for pair in eng_api_list:
        if random() < prob_boundary:
            dev.append(pair)
        else:
            train.append(pair)
    return train, dev


def parse_file_to_eng_and_api(filename):
    eng_api = []
    # unwanted_comments = [
    #     'Required method for Designer support - do not modify  the contents of this method with the code editor.',
    #     'Clean up any resources being used.',
    #     'The main entry point for the application.']
    designer_comment_start = 'Required method for Designer'
    with open(filename, "r", encoding='utf-8') as f:
        while True:
            line = f.readline().strip()
            if line == '':
                break
            if line[0] == '*' or line[0] == '/':
                continue
            # if line.startswith("*") or line.startswith("/"):
            if langid.classify(line)[0] != 'en' or line.startswith(designer_comment_start):
                api_line = f.readline()  # we won't need it
                continue

            cur_eng = line.split(" ")
            line = f.readline().strip()
            cur_api = line.split(" ")

            if not (len(cur_api) == 0 or len(cur_eng) == 0):
                eng_api.append((cur_eng, cur_api))
    return eng_api
    # if ifcleanup:
    #     api_dict = None
    #     if leave_only_system:
    #         _, api_desc = zip(*eng_api)
    #         api_dict = create_dict_on_condition(api_desc, lambda x: x.startswith("System.") or x.count('.') == 1)
    #     eng_api = clean_up_sentences(eng_api, api_dict, if_remove_repetitions=True)
    #
    # # make every pair unique
    # # temp = set(zip(map((lambda x: tuple(x)), english_desc), map((lambda x: tuple(x)), api_desc)))
    # return list(set(map((lambda x: (tuple(x[0]), tuple(x[1]))), eng_api)))
    # english_desc, api_desc = zip(*list(temp))

    # no writing to files!

    # return english_desc, api_desc


def improve_eng_api(eng_api, ifcleanup=True, leave_only_system=False):
    if ifcleanup:
        api_dict = None
        if leave_only_system:
            _, api_desc = zip(*eng_api)
            api_dict = create_dict_on_condition(api_desc, lambda x: x.startswith("System.") or x.count('.') == 1)
        eng_api = clean_up_sentences(eng_api, api_dict, if_remove_repetitions=True)

    return list(set(map((lambda x: (tuple(x[0]), tuple(x[1]))), eng_api)))


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

    eng_api = parse_file_to_eng_and_api(filename=res_files[0])
    eng_api = improve_eng_api(eng_api)
    for res_file in res_files[1:]:
        print('parsing ' + res_file)
        eng_api_new = parse_file_to_eng_and_api(filename=res_file)
        eng_api_new = improve_eng_api(eng_api_new)
        eng_api += eng_api_new

    train, dev = separate_to_train_and_dev(eng_api)
    # remove_empty_lines.remove_pair_where_one_is_empty(train)
    # remove_empty_lines.remove_pair_where_one_is_empty(dev)
    eng_train, api_train = zip(*train)
    eng_dev, api_dev = zip(*dev)
    return (eng_train, eng_dev), (api_train, api_dev)



def parse_database_to_train_and_test():
    eng_api = parse_database_to_eng_and_api()
    eng_api = improve_eng_api(eng_api)

    train, dev = separate_to_train_and_dev(eng_api)
    # remove_empty_lines.remove_pair_where_one_is_empty(train)
    # remove_empty_lines.remove_pair_where_one_is_empty(dev)
    eng_train, api_train = zip(*train)
    eng_dev, api_dev = zip(*dev)
    return (eng_train, eng_dev), (api_train, api_dev)


def create_vocab(sentences, vocab_size, skip_first_n_words):
    vocab = {}
    for sentence in sentences:
        for w in sentence:
            if w in vocab:
                vocab[w] += 1
            else:
                vocab[w] = 1
    vocab_list = sorted(vocab, key=vocab.get, reverse=True)
    if len(vocab_list) > vocab_size:
        vocab_list = vocab_list[skip_first_n_words:vocab_size]
    return vocab_list


# def create_vocab_from_file(input_file, vocab_size):
#     print("Creating vocabulary from data %s" % (input_file))
#     with open(input_file, mode="r", encoding='utf-8') as f:
#         return create_vocab(f, vocab_size)

def filter_list_of_lists_by_vocab(list_of_lists, vocab):
    vocab = set(vocab)
    temp = [list(sentence) for sentence in list_of_lists]
    for sentence in temp:
        sentence[:] = [word for word in sentence if word in vocab]
    return [sentence for sentence in temp if len(sentence) > 0]


def filter_eng_api_by_vocabs(eng, api, vocab_eng, vocab_api):
    vocab_eng = set(vocab_eng)
    vocab_api = set(vocab_api)
    res_e = []
    res_a = []
    for (eng_sent, api_sent) in zip(eng, api):
        e = [word for word in eng_sent if word in vocab_eng]
        a = [word for word in api_sent if word in vocab_api]
        if len(e) > 1 and len(a) > 0:
            res_e.append(e)
            res_a.append(a)
    return res_e, res_a


def write_two_vocabs(eng_vocab, api_vocab, eng_size, api_size, vocab_postfix=''):
    utils.write_lines_to_file('vocab' + str(eng_size) + '_test' + vocab_postfix + '.from', eng_vocab)
    utils.write_lines_to_file('vocab' + str(api_size) + '_test' + vocab_postfix + '.to', api_vocab)


if __name__ == "__main__":
    # a = [('ab', 'cd'), ('ef')]
    # b = [('b', 'd'), ('f')]
    # c = zip(*zip(a, b))
    # a = [1, 3, 5, 5, 6, 7, 8]
    # b = a[1:]
    # c = a[:-1]
    train_eng_file = 'trainB.eng'
    train_api_file = 'trainB.api'
    test_eng_file = 'testB.eng'
    test_api_file = 'testB.api'
    # (eng_train_samples, eng_test_samples), (api_train_samples, api_test_samples) = parse_res_files_to_train_and_test(res_files_count=24)
    (eng_train_samples, eng_test_samples), (api_train_samples, api_test_samples) = parse_database_to_train_and_test()

    eng_vocab_size = 10000
    eng_vocab = create_vocab(eng_train_samples, eng_vocab_size, 7)
    api_vocab_size = 10000
    api_vocab = create_vocab(api_train_samples, api_vocab_size, 0)

    write_two_vocabs(eng_vocab, api_vocab, eng_vocab_size, api_vocab_size, vocab_postfix='max+dict1000+noAPIrepeat')

    # eng_train_samples = filter_list_of_lists_by_vocab(eng_train_samples, eng_vocab)
    # eng_test_samples = filter_list_of_lists_by_vocab(eng_test_samples, eng_vocab)
    # api_train_samples = filter_list_of_lists_by_vocab(api_train_samples, api_vocab)
    # api_test_samples = filter_list_of_lists_by_vocab(api_test_samples, api_vocab)
    eng_train_samples, api_train_samples = filter_eng_api_by_vocabs(eng_train_samples, api_train_samples, eng_vocab,
                                                                    api_vocab)
    eng_test_samples, api_test_samples = filter_eng_api_by_vocabs(eng_test_samples, api_test_samples, eng_vocab,
                                                                  api_vocab)

    write_all_train_data_to_files(eng_train_samples, api_train_samples, train_eng_file, train_api_file,
                                  ifoverwrite=True)
    write_all_train_data_to_files(eng_test_samples, api_test_samples, test_eng_file, test_api_file, ifoverwrite=True)


    # test_stuff()
    # parse_file_write_to_2_files("/tmp/res1.txt","eng_dev.txt", "api_dev.txt")
    # parse_file_write_to_2_files("/tmp/res_3.txt","eng_dev.txt", "api_dev.txt")
    # create_vocab("eng_dev.txt", 'vocab' + str(10000) + '.from', 10000)
    # create_vocab("api_dev.txt", 'vocab' + str(10000) + '.to', 10000)

    # 4489200 of not unique pairs
