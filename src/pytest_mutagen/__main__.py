import sys
import os
import parso
import argparse
import hashlib
from os import path
from py.io import TerminalWriter

RED   = "\033[1;37;41m"
BLUE  = "\033[1;34m"
CYAN  = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"

all_mutants = {}
current_func = None
current_class = None
mutant_count = 0

class StrMutant:
    def __init__(self, name, func_name, start_pos, end_pos, new_str):
        self.name = name
        self.func_name = func_name
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.new_str = new_str
    def __str__(self):
        return "[" + self.func_name + " | " + str(self.start_pos) + " --> " + str(self.end_pos) + \
            ": " + self.new_str + "]"
    @property
    def hash(self):
        s = ":".join((self.name, self.func_name, str(self.start_pos), str(self.end_pos), self.new_str))
        return hashlib.shake_128(str.encode(s)).hexdigest(8)

def get_func_name(function_node):
    prefix = "" if current_class is None else current_class.name.value + "."
    return prefix + function_node.name.value

def find_mutants(node):
    global current_func
    global current_class
    global mutant_count

    for child in node.children:
        if child.type == "funcdef":
            current_func = child
            mutant_count = 0
            find_mutants_rec(child.get_suite())
            current_func = None
        elif child.type == "classdef":
            current_class = child
            find_mutants(child.get_suite())
            current_class = None
            continue

def relative_positions(start, end, func):
    start_pos = (start[0] - func.start_pos[0], start[1] - func.start_pos[1])
    end_pos = (end[0] - func.start_pos[0], end[1] - func.start_pos[1])
    return (start_pos, end_pos)


def find_mutants_rec(node):
    global all_mutants
    global current_func
    global mutant_count

    current_func_name = get_func_name(current_func)
    for child in node.children:
        start_pos, end_pos, new_str = None, None, ""
        if child.type in ["funcdef", "suite", "simple_stmt", "expr_stmt", "comparison"]:
            find_mutants_rec(child)
            continue
        if child.type == "if_stmt":
            # "if not condition:" ---> "if condition:"
            if child.children[1].type == "not_test":
                keyword_not = child.children[1].children[0]

                start_pos, end_pos = relative_positions(keyword_not.start_pos, keyword_not.end_pos, current_func)
                new_str = ""
            # "if condition:" ---> "if not (condition):"
            else:
                keyword = child.children[0]
                condition = child.children[1]
                start_pos, end_pos = relative_positions(keyword.end_pos, condition.end_pos, current_func)

                condition_code = condition.get_code()
                if condition_code[0] == ' ':
                    condition_code = condition_code[1:]
                    start_pos = start_pos[0], start_pos[1] + 1
                elif condition_code[0] == '(':
                    assert condition_code[-1] == ')'
                    condition_code = condition_code[1:-1]
                    new_str = " "

                new_str += "not (" + condition_code + ")"
        # any right value ---> None
        elif child.type == "operator" and child.value == "=" and not (child.get_next_sibling().type == "keyword" and child.get_next_sibling().value == "None"):
            start_pos, end_pos = relative_positions(child.end_pos, child.parent.end_pos, current_func)
            start_pos = start_pos[0], start_pos[1] + 1
            new_str = "None"

        # operators switch
        elif child.type == "operator":
            operator_mutations = {
                    '+': '-',
                    '-': '+',
                    '*': '/',
                    '/': '*',
                    '//': '/',
                    '%': '/',
                    '<<': '>>',
                    '>>': '<<',
                    '&': '|',
                    '|': '&',
                    '^': '&',
                    '**': '*',
                    '~': '',

                    '+=': '-=',
                    '-=': '+=',
                    '*=': '/=',
                    '/=': '*=',
                    '//=': '/=',
                    '%=': '/=',
                    '<<=': '>>=',
                    '>>=': '<<=',
                    '&=': '|=',
                    '|=': '&=',
                    '^=': '&=',
                    '**=': '*=',
                    '~=': '=',

                    '<': '<=',
                    '<=': '<',
                    '>': '>=',
                    '>=': '>',
                    '==': '!=',
                    '!=': '==',
                    '<>': '==',
                }
            if child.value in operator_mutations:
                start_pos, end_pos = relative_positions(child.start_pos, child.end_pos, current_func)
                new_str = operator_mutations[child.value]
        # return ... ---> pass
        # and the content od the return can be mutated too
        elif child.type == "return_stmt":
            start_pos, end_pos = relative_positions(child.start_pos, child.end_pos, current_func)
            new_str = "pass"
            find_mutants_rec(child)

        if start_pos is not None:
            str_mutant = StrMutant(current_func_name.upper()+"_"+str(mutant_count), current_func_name, start_pos, end_pos, new_str)
            mutant_count += 1
            if current_func_name not in all_mutants:
                all_mutants[current_func_name] = [str_mutant]
            else:
                all_mutants[current_func_name].append(str_mutant)

def print_enlight(func_code, mutant, color):
    start = mutant.start_pos
    end = mutant.end_pos

    for i, line in enumerate(func_code):
        if i == start[0]:
            print(line[:start[1]] + color + line[start[1]:end[1]] + RESET + line[end[1]:])
        else:
            print(line)

def write_to_mutation_file(output_file, func_code, mutant):
    file = open(output_file, "a")

    file.write("#hash=" + mutant.hash + "\n")
    file.write("@mg.mutant_of(\"" + mutant.func_name + "\", \"" + mutant.name + "\")\n")
    start = mutant.start_pos
    end = mutant.end_pos

    for i, line in enumerate(func_code):
        if i == 0:
            file.write("def" + line[3:].replace(mutant.func_name, mutant.name.lower(), 1) + "\n")
        elif i == start[0]:
            file.write(line[:start[1]] + mutant.new_str + line[end[1]:] + "\n")
        else:
            file.write(line + "\n")

    file.close()

def make_valid_import(file, module):
    assert file[-3:] == ".py"

    return path.join(path.basename(module), path.relpath(file, start=module)).replace("/", ".")[:-3]

def check_already_written(filename):
    global all_mutants
    hash_list = []

    with open(filename, "r") as file:
        lines = file.read().split("\n")
        for l in lines:
            if l.startswith("#hash="):
                hash_list.append(l[6:])
    return hash_list

def main():
    global all_mutants

    parser = argparse.ArgumentParser(description="Suggest mutants to the user that can keep them or delete them.\n\
                                        The kept mutants are written to a file and ready to use with pytest-mutagen")
    parser.add_argument('input_path',
                        help='path to the file or directory to mutate')
    parser.add_argument('-o', '--output-path', default=None,
                        help='path to the file or directory where the mutants should be written')
    parser.add_argument('-m', '--module-path', default=None,
                        help='path to the module directory (location of __init__.py) for import purposes')
    args = parser.parse_args()
    input_file_path = args.input_path
    output_path = args.output_path if args.output_path else "mutations_"+path.basename(input_file_path)

    if path.isdir(input_file_path):
        for root, dirs, files in os.walk(input_file_path, topdown=True):
            for filename in files:
                if filename.endswith('.py'):
                    module_path = args.module_path if args.module_path else input_file_path
                    mutate_file(os.path.join(root, filename), \
                        path.join(output_path, "mutations_" + filename) if path.isdir(output_path) else "mutations_" + filename,\
                        module_path)
    else:
        module_path = args.module_path if args.module_path else path.dirname(input_file_path)
        mutate_file(input_file_path, path.join(output_path, "mutations.py") if path.isdir(output_path) else output_path, module_path)

def get_imports():
    global all_mutants
    imports = []

    for func in all_mutants.keys():
        if '.' in func:
            l = func.split('.')
            if l[0] not in imports:
                imports.append(l[0])
        else:
            imports.append(func)

    return imports


def mutate_file(input_file_path, output_file_name, module_path):
    global all_mutants

    input_file = open(input_file_path, "r")
    content = input_file.read()
    input_file.close()

    all_mutants = {}
    already_written_hash = []
    tree = parso.parse(content)
    find_mutants(tree)
    if len(all_mutants) == 0:
        return

    TerminalWriter().sep("=", path.basename(input_file_path))

    if path.isfile(output_file_name):
        print(CYAN + "The file", output_file_name, "already exists.")
        print("\t(r) reset")
        print("\t(c) continue where it stopped")
        print("\t(a) abort" + RESET)
        answer = input()
        while answer not in ["r", "a", "c"]:
            answer = input("Invalid choice, try again: ")

        if answer == "r":   # reset
            output_file = open(output_file_name, "w")
            output_file.write("import pytest_mutagen as mg\n")
            output_file.write("import " + path.basename(module_path) + "\n")
            output_file.write("from " + make_valid_import(input_file.name, module_path) + " import ")
            output_file.write(", ".join(get_imports()))
            output_file.write("\n\n")
            output_file.write("mg.link_to_file(mg.APPLY_TO_ALL)\n\n")
            output_file.close()
        elif answer == "a": # abort
            return
        elif answer == "c": # continue
            already_written_hash = check_already_written(output_file_name)

    for child in tree.children:
        if child.type == "funcdef":
            mutate_function(child, output_file_name, already_written_hash)
        elif child.type == "classdef":
            mutate_class(child, output_file_name, already_written_hash)

    print("Mutants written to", output_file_name)
    all_mutants = {}

def mutate_class(child, output_file_name, already_written_hash):
    global current_class

    TerminalWriter().sep(".", child.name.value)

    current_class = child
    for c in child.get_suite().children:
        if c.type == "funcdef":
            mutate_function(c, output_file_name, already_written_hash)
    current_class = None

    TerminalWriter().sep(".")

def remove_unnecessary_spaces(func_code):
    empty_lines = 0
    for line in func_code:
        if line == "":
            empty_lines += 1
        else:
            break
    func_code = func_code[empty_lines:]
    offset = func_code[0].find("def")
    assert offset != -1

    return [line[offset:] for line in func_code]


def mutate_function(child, output_file_name, already_written_hash):
    global all_mutants

    func_code = child.get_code().split("\n")
    func_name = get_func_name(child)

    func_code = remove_unnecessary_spaces(func_code)

    for i, mutant in enumerate(all_mutants.get(func_name, [])):
        title = "# Function " + func_name + " #"

        if mutant.hash in already_written_hash:
            continue

        print()
        print("#"*len(title))
        print(title)
        print("#"*len(title))
        print("\nMutant:", GREEN + mutant.new_str + RESET)
        print()

        print_enlight(func_code, mutant, RED)
        print(CYAN + "\tKeep? (n to delete)" + RESET, end="\t")
        answer = input()

        if answer == "n":
            del mutant
        else:
            write_to_mutation_file(output_file_name, func_code, mutant)

if __name__=="__main__":
    main()