import os
import zlib
import re


def get_hash(hash_value, folder):
    path = os.path.join(folder, hash_value[:2], hash_value[2:])
    with open(path, "rb") as f:
        data = zlib.decompress(f.read())
    return data


def parse_hash(hash_value, hash_r):
    text = ""
    not_founded = True
    table = (str(hash_value)[2:-1]).split()
    normal_table = []
    if table[0] == "tree":
        normal_table.append(table[0])
        normal_table.append(hash_r)
        for m in table[2]:
            if text[-4:] == "\\x00" and not_founded:
                normal_table.append(text[:-4])
                text = ""
                not_founded = False
            text += m
        normal_table.append(text)
    elif table[0] == "commit":
        for elem in table:
            if elem == table[0]:
                continue
            elem = re.sub(r'^(\d+)\\x00', '', elem)
            elem = re.sub(r'\\x\w{2}', '', elem)
            elem = re.sub(r'(\\n){2}', ' message:', elem)
            elem = re.sub(r'\\[ntr]', ' ', elem)
            text += elem
            text += " "
        normal_table = text[:-1].split()
        normal_table.insert(0, table[0])
        normal_table.insert(1, hash_r)
        not_founded = True
        text = ""
        first_index = 0
        for j in range(len(normal_table)):
            if not_founded:
                first_index = j
            if normal_table[j][:8] == "message:" or (not_founded is False):
                text += " " + normal_table[j]
                not_founded = False
        while first_index != len(normal_table):
            normal_table.pop(first_index)
        normal_table.append(text[9:])
    else:
        normal_table.append(table[0])
        normal_table.append(hash_r)
        for elem in table:
            if elem == table[0]:
                continue
            elem = re.sub(r'^(\d+)\\x00', '', elem)
            elem = re.sub(r'\\x\w{2}', '', elem)
            elem = re.sub(r'\\[ntr]', '', elem)
            text += elem
            text += " "
        normal_table.append(text[:-1])
    return normal_table


def search_elements():
    elements = []
    git_folder = ".git/objects"
    for root, dirs, files in os.walk(git_folder):
        if root != git_folder:
            parent_folder = os.path.basename(root)
            if parent_folder not in ['info', 'pack']:
                for file_t in files:
                    elements.append(parse_hash(get_hash(parent_folder + file_t, git_folder), parent_folder + file_t))
    return elements


def equals_obj(a, b):
    final = a
    final = re.sub(r'<\w', "", final)
    final = re.sub(r'[\\x[A-Z\W]', " ", final)
    elements = final.split()
    cnt = 0
    for r in range(len(elements)):
        if len(elements[r]) == 2:
            match = re.search(elements[r][:2], b)
            if match:
                cnt += 1
        else:
            cnt += 1
    if len(elements) == cnt:
        return True
    return False


def generate_dot_graph(elements_of_graph_arg):
    dot_header = "digraph GitGraph {\n"
    dot_footer = "}"
    dot_body = ""
    commits = []
    trees = []
    objects = []
    for k in elements_of_graph_arg:
        if k[0] == "commit":
            dot_body += "   " + "\"" + k[-1] + " (" + k[1][:6] + ")" + "\"" + " [shape=box][color=orange];\n"
            k.append("\"" + k[-1] + " (" + k[1][:6] + ")" + "\"")
            commits.append(k)
        elif k[0] == "tree":
            dot_body += "   " + "\"" + k[2] + " (" + k[1][:6] + ")" + "\"" + " [shape=box][color=blue];\n"
            k.append("\"" + k[2] + " (" + k[1][:6] + ")" + "\"")
            trees.append(k)
        else:
            dot_body += "   " + "\"\'" + k[2] + "\'\"" + " [color=black];\n"
            k.append("\"\'" + k[2] + "\'\"")
            objects.append(k)
    for kid in commits:
        if kid[4] == "parent":
            for parent in commits:
                if kid[5] == parent[1]:
                    dot_body += "   " + parent[-1] + " -> " + kid[-1] + "\n"
    for commit in commits:
        dot_body += "   " + commit[-1] + " -> "
        for tree in trees:
            if commit[3] == tree[1]:
                dot_body += tree[-1] + " -> "
                for obj in objects:
                    if equals_obj(tree[-2], obj[1]):
                        dot_body += obj[-1] + ";\n"

    return dot_header + dot_body + dot_footer


if __name__ == "__main__":
    elements_of_graph = search_elements()
    elements_of_graph.sort()
    with open("git_graph.dot", "w") as file:
        file.write(generate_dot_graph(elements_of_graph))
