import operator

from my_utils import clean_up_sentences, create_dict_on_condition


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
        api_dict = create_dict_on_condition(api_desc, lambda x: x.startswith("System.") or x.count('.') == 1)
        clean_up_sentences(list(zip(english_desc, api_desc)), api_dict)
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
            if len(x) == 0 or len(y) == 0:
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
