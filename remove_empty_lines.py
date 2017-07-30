from my_utils import write_all_train_data_to_files


def remove_pair_where_one_is_empty(pairs):
    res = []
    i = 0
    for pair in pairs:
        if len(pair[0]) == 0 or len(pair[1]) == 0:
            print('empty line!')
            i += 1
            print(i)
            continue
        res.append(pair)
    return res

def shorten_file(path):
    with open(path) as f:
        lines = [s.strip().split(" ") for s in f.readlines()]
        lines = [line[:50] if len(line) > 50 else line for line in lines]
    with open(path, 'w') as f:
        for line in lines:
            f.write(" ".join(line) + "\n")

def remove_empty():
    eng = []
    api = []
    engpath = "eng_test_dev.txt"
    apipath = "api_test_dev.txt"
    with open(engpath) as f:
        eng = [s.strip() for s in f.readlines()]
    with open(apipath) as f:
        api = [s.strip() for s in f.readlines()]

    temp = remove_pair_where_one_is_empty(list(zip(eng, api)))
    (eng, api) = zip(*temp)

    engfile="test.eng"
    apifile="test.api"
    with open(engfile, 'w') as f:
        for e in eng:
            f.write(e + "\n")

    with open (apifile, 'w') as f:
        for a in api:
            f.write(a + "\n")

paths = ["train1.eng", "train1.api", "test1.eng", "test1.api"]
for path in paths:
    shorten_file(path)
# shorten_file("test.api")
# remove_empty()