from re import finditer

def camel_case_split(identifier):
    matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]

def find_char_from_end(s, c_target, num_to_return):
    c_encounters = 0
    indices = []
    for i, c in enumerate(reversed(s)):
        if c != c_target:
            continue
        c_encounters += 1
        indices.append(len(s) - i)
        if c_encounters == num_to_return:
            return indices
    return indices

def name_to_tokens(name):
    dot_indices = find_char_from_end(name, '.', 2)
    if len(dot_indices) == 0:
        return None
    if len(dot_indices) == 1:
        class_name = name[:dot_indices[0] - 1]
        method_name = name[dot_indices[0]:]
    else:
        class_name = name[dot_indices[1]:dot_indices[0] - 1]
        method_name = name[dot_indices[0]:]
    return list(map((lambda x: x.lower()), camel_case_split(class_name))) + \
        list(map((lambda x: x.lower()), camel_case_split(method_name)))

if __name__ == 'main':
    print(name_to_tokens('smthOne.FourFive'))