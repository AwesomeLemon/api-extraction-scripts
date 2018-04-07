
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
            if langid.classify(line)[0] != 'en':  # or line.startswith(designer_comment_start):
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