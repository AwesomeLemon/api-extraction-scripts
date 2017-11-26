# coding=utf-8
import string
from random import random
import langid
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.stem import PorterStemmer
from langdetect import detect

import remove_empty_lines
import utils
from database import parse_database_to_eng_and_api, store_repos, parse_database_to_names_and_api


def create_dict_on_condition(sentence_list, predicate):
    word_set = set()
    for sentence in sentence_list:
        for word in sentence:
            if predicate(word):
                word_set.add(word)
    return word_set


def clean_up_sentences(list_of_sentence_pairs, api_dict=None, if_shorten=False, if_remove_repetitions=False, if_stem=False):
    # lemmatizer = WordNetLemmatizer()
    stemmer = PorterStemmer()

    def clean_up_eng(sentence_eng):
        sentence_eng = sentence_eng.translate(str.maketrans('-', ' '))
        sentence_eng = sentence_eng.translate(str.maketrans('', '', string.punctuation))
        sentence_eng = sentence_eng.split(' ')
        if if_stem:
            sentence_eng = [stemmer.stem(word.lower())
                               for word in sentence_eng if len(word) < 20]
        else:
            sentence_eng = [word.lower() for word in sentence_eng if len(word) < 20]
        return [word for word in sentence_eng if len(word) > 0]
        # for i, word in enumerate(words):
        #     words[i] = word.lower().translate(None, string.punctuation)

    def clean_api_by_dict(sentence_api):
        return [call for call in sentence_api if call in api_dict]

    def clean_api_shorten(sentence_api):
        sentence_word_boundary = 10
        if len(sentence_api) >= sentence_word_boundary:
            words_at_ends_to_keep = 3
            start = sentence_api[:words_at_ends_to_keep]
            end = sentence_api[len(sentence_api) - words_at_ends_to_keep:]
            sentence_api[:] = start + end
        return sentence_api

    def clean_api_consecutive_repetitions(sentence_api):
        prev = None
        res = []
        for word in sentence_api:
            if word != prev:
                res.append(word)
            prev = word
        return res

    def clean_api_global_namespace(sentence_api):
        new_api = []
        delete_next = 0
        for call in sentence_api:
            if delete_next > 0:
                delete_next -= 1
                continue
            if call == '<global':
                delete_next = 1
                continue
            new_api.append(call)
        return new_api

    designer_comment_start = 'Required method for Designer'
    clean_comment_start = 'Clean up any resources being used'
    support_by_comment_start = 'SupportByVersion'
    main_entry_comment_start = 'Main entry point'
    cleaned_sentences = []
    for sentence_pair in list_of_sentence_pairs:
        eng = sentence_pair[0]
        if eng.startswith(designer_comment_start) or eng.startswith(support_by_comment_start) \
                or eng.startswith(clean_comment_start) or eng.startswith(main_entry_comment_start):
                 continue
        cleaned_eng = clean_up_eng(eng)
        api = sentence_pair[1].split(' ')
        api = clean_api_global_namespace(api)
        if api_dict is not None:
            api = clean_api_by_dict(api)
        if if_shorten:
            api = clean_api_shorten(api)
        if if_remove_repetitions:
            api = clean_api_consecutive_repetitions(api)
        if len(cleaned_eng) > 0 and len(api) > 0:
            cleaned_sentences.append((cleaned_eng, api))

    return cleaned_sentences


def separate_to_train_and_dev(eng_api_list):
    total = len(eng_api_list)
    test_size = 20000.0
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
    # designer_comment_start = 'Required method for Designer'
    with open(filename, "r", encoding='utf-8') as f:
        while True:
            line = f.readline().strip()
            if line == '':
                break
            if line[0] == '*' or line[0] == '/':
                continue
            # if line.startswith("*") or line.startswith("/"):
            if langid.classify(line)[0] != 'en': #or line.startswith(designer_comment_start):
                api_line = f.readline()  # we won't need it
                continue

            cur_eng = line
            cur_api = f.readline().strip()

            eng_api.append((cur_eng, cur_api))
    return eng_api


def parse_file_to_strings_eng_and_api(filename):
    eng_api = []
    with open(filename, "r", encoding='utf-8') as f:
        while True:
            try:
                line = f.readline().strip()
                if line == '':
                    break
                if line[0] == '*' or line[0] == '/':
                    continue

                if detect(line) != 'en':
                    line = f.readline()
                    continue

                cur_eng = line
                cur_api = f.readline().strip()
                eng_api.append((cur_eng, cur_api))
            except:
                pass
    return eng_api


def parse_file_to_repo_names_with_methods(filename):
    def find_slashes(s):
        return [i for i, ltr in enumerate(s) if ltr == '\\']

    def find_segment(slash_indices, target):
        i = 0
        while slash_indices[i] < target:
            i += 1
        return slash_indices[i - 1], slash_indices[i]

    def get_repo_name(line):
        slash_indices = find_slashes(line)
        underscore_index = line.find('_')
        surrounding_slashes = find_segment(slash_indices, underscore_index)
        return line[surrounding_slashes[0] + 1: surrounding_slashes[1]]

    repo_names = []
    with open(filename, "r", encoding='utf-8') as f:
        prev_repo_ind = -1
        cur_ind = 0
        while True:
            cur_ind += 1
            line = f.readline().strip()
            if line == '':
                break
            if not (line[0:2] == '**' and line[-4:] == '.sln'):
                continue
            if cur_ind == prev_repo_ind + 1:
                del repo_names[-1]
            prev_repo_ind = cur_ind
            repo_names.append(get_repo_name(line))
    return repo_names


def parse_file_to_method_names(filename):
    method_names = []
    with open(filename, "r", encoding='utf-8') as f:
        while True:
            line = f.readline().strip()
            if line == '':
                break
            if not line[0:2] == '//':
                continue
            method_names.append(line[2:])
    return method_names


def improve_eng_api(eng_api, ifcleanup=True, leave_only_system=False, make_unique=True, if_stem=False):
    if ifcleanup:
        api_dict = None
        if leave_only_system:
            _, api_desc = zip(*eng_api)
            api_dict = create_dict_on_condition(api_desc, lambda x: x.startswith("System.") or x.count('.') == 1)
        eng_api = clean_up_sentences(eng_api, api_dict, if_remove_repetitions=True, if_stem=if_stem)
    if make_unique:
        print('before unique: ' + str(len(eng_api)))
        return list_to_unique(eng_api)
    return eng_api


def list_to_unique(eng_api):
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

    return to_separate_eng_api_train_dev(eng_api)

def parse_res_files_to_cleaned_eng_api(res_files=None, res_files_count=2, res_files_first=1):
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

    return eng_api


def parse_res_files_to_repo_names(res_files=None, res_files_count=24, res_files_first=1):
    if res_files is None:
        res_files = ['/tmp/res' + str(i) + '.txt' for i in
                     range(res_files_first, res_files_count + 1)]  # ['/tmp/res1.txt', '/tmp/res2.txt']

    repo_names = parse_file_to_repo_names_with_methods(filename=res_files[0])
    for res_file in res_files[1:]:
        print('parsing ' + res_file)
        repo_names_new = parse_file_to_repo_names_with_methods(filename=res_file)
        repo_names += repo_names_new

    repo_names = ['https://github.com/' + rn.replace('_', '/') + '.git' for rn in repo_names]
    return repo_names


def parse_res_files_to_method_names(res_files=None, res_files_count=24, res_files_first=1):
    if res_files is None:
        res_files = ['/tmp/res' + str(i) + '.txt' for i in
                     range(res_files_first, res_files_count + 1)]  # ['/tmp/res1.txt', '/tmp/res2.txt']

    method_names = parse_file_to_method_names(filename=res_files[0])
    for res_file in res_files[1:]:
        print('parsing ' + res_file)
        method_names_new = parse_file_to_method_names(filename=res_file)
        method_names += method_names_new

    print(len(method_names))
    # method_names = ['https://github.com/' + rn.replace('_', '/') + '.git' for rn in set(method_names)]
    return set(method_names)


def parse_res_files_to_string_eng_api(res_files=None, res_files_count=24, res_files_first=1):
    if res_files is None:
        res_files = ['/tmp/res' + str(i) + '.txt' for i in
                     range(res_files_first, res_files_count + 1)]  # ['/tmp/res1.txt', '/tmp/res2.txt']

    eng_api = parse_file_to_strings_eng_and_api(filename=res_files[0])
    for res_file in res_files[1:]:
        print('parsing ' + res_file)
        method_names_new = parse_file_to_strings_eng_and_api(filename=res_file)
        eng_api += method_names_new

    print(len(eng_api))
    # return list(set(map((lambda x: (tuple(x[0]), tuple(x[1]))), eng_api)))
    return set(eng_api)


def parse_database_comments_to_train_and_test():
    eng_api = parse_database_to_eng_and_api()
    eng_api = improve_eng_api(eng_api, if_stem=True)

    return to_separate_eng_api_train_dev(eng_api)

def parse_database_names_to_train_and_test():
    eng_api = parse_database_to_names_and_api()
    eng_api = improve_eng_api(eng_api, if_stem=True)

    return to_separate_eng_api_train_dev(eng_api)


def to_separate_eng_api_train_dev(eng_api):
    train, dev = separate_to_train_and_dev(eng_api)
    eng_train, api_train = zip(*train)
    eng_dev, api_dev = zip(*dev)
    return (eng_train, eng_dev), (api_train, api_dev)


def parse_database_to_cleaned_eng_api():
    eng_api = parse_database_to_eng_and_api()
    eng_api = improve_eng_api(eng_api)

    return eng_api

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
    utils.write_lines_to_file('vocab' + str(eng_size) + '_' + vocab_postfix + '.from', eng_vocab)
    utils.write_lines_to_file('vocab' + str(api_size) + '_' + vocab_postfix + '.to', api_vocab)

def merge_files_and_database(eng_api_files, eng_api_database):
    eng_api = eng_api_files + eng_api_database
    print('before unique: ' + str(len(eng_api)))
    eng_api = list_to_unique(eng_api)
    return to_separate_eng_api_train_dev(eng_api)

if __name__ == "__main__":
    # # repo_names = parse_res_files_to_repo_names(['/home/jet/Downloads/res17.txt'])
    # repo_names = parse_res_files_to_repo_names()
    # with open('reps.txt', 'w') as file_handler:
    #     for item in repo_names:
    #         file_handler.write("{}\n".format(item))
    # method_names = parse_res_files_to_method_names()
    # string_eng_api = parse_res_files_to_string_eng_api()
    # store_repos(repo_names)
    # a = [('ab', 'cd'), ('ef')]
    # b = [('b', 'd'), ('f')]
    # c = zip(*zip(a, b))
    # a = [1, 3, 5, 5, 6, 7, 8]
    # b = a[1:]
    # c = a[:-1]
    dataset_index = 'H0'
    train_eng_file = 'train' + dataset_index + '.eng'
    train_api_file = 'train'+dataset_index+'.api'
    test_eng_file = 'test'+dataset_index+'.eng'
    test_api_file = 'test'+dataset_index+'.api'
    # (eng_train_samples, eng_test_samples), (api_train_samples, api_test_samples) = parse_res_files_to_train_and_test(res_files_count=24)
    (eng_train_samples, eng_test_samples), (api_train_samples, api_test_samples) = parse_database_names_to_train_and_test()
    # (eng_train_samples, eng_test_samples), (api_train_samples, api_test_samples) = parse_database_comments_to_train_and_test()
    #Merged dataset:
    # eng_api_files = parse_res_files_to_cleaned_eng_api(res_files_count=24)
    # eng_api_database = parse_database_to_cleaned_eng_api()
    # (eng_train_samples, eng_test_samples), (api_train_samples, api_test_samples) = merge_files_and_database(eng_api_files, eng_api_database)
    eng_vocab_size = 10000
    eng_vocab = create_vocab(eng_train_samples, eng_vocab_size, 0)
    api_vocab_size = 10000
    api_vocab = create_vocab(api_train_samples, api_vocab_size, 0)

    write_two_vocabs(eng_vocab, api_vocab, eng_vocab_size, api_vocab_size,
                     vocab_postfix='db_comments_stem')

    # eng_train_samples = filter_list_of_lists_by_vocab(eng_train_samples, eng_vocab)
    # eng_test_samples = filter_list_of_lists_by_vocab(eng_test_samples, eng_vocab)
    # api_train_samples = filter_list_of_lists_by_vocab(api_train_samples, api_vocab)
    # api_test_samples = filter_list_of_lists_by_vocab(api_test_samples, api_vocab)
    print('before vocab frequency filtering: ' + str(len(eng_train_samples)))
    eng_train_samples, api_train_samples = filter_eng_api_by_vocabs(eng_train_samples, api_train_samples, eng_vocab,
                                                                    api_vocab)
    eng_test_samples, api_test_samples = filter_eng_api_by_vocabs(eng_test_samples, api_test_samples, eng_vocab,
                                                                  api_vocab)

    print('after vocab frequency filtering: ' + str(len(eng_train_samples)))

    write_all_train_data_to_files(eng_train_samples, api_train_samples, train_eng_file, train_api_file,
                                  ifoverwrite=True)
    write_all_train_data_to_files(eng_test_samples, api_test_samples, test_eng_file, test_api_file, ifoverwrite=True)


    # test_stuff()
    # parse_file_write_to_2_files("/tmp/res1.txt","eng_dev.txt", "api_dev.txt")
    # parse_file_write_to_2_files("/tmp/res_3.txt","eng_dev.txt", "api_dev.txt")
    # create_vocab("eng_dev.txt", 'vocab' + str(10000) + '.from', 10000)
    # create_vocab("api_dev.txt", 'vocab' + str(10000) + '.to', 10000)

    # 4489200 of not unique pairs
