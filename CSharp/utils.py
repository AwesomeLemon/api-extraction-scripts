def write_lines_to_file(path, list):
    with open(path, mode="w", encoding='utf-8') as file:
        for w in list:
            file.write(w + "\n")