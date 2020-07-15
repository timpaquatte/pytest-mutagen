import sys
import parso
import argparse
from os import path

RED   = "\033[1;37;41m"
BLUE  = "\033[1;34m"
CYAN  = "\033[1;36m"
GREEN = "\033[0;32m"
RESET = "\033[0;0m"

all_mutants = {}
current_func = None

class StrMutant:
    def __init__(self, func_name, start_pos, end_pos, new_str):
        self.func_name = func_name
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.new_str = new_str
    def __str__(self):
        return "[" + self.func_name + " | " + str(self.start_pos) + " --> " + str(self.end_pos) + \
            ": " + self.new_str + "]"

def get_func_name(function_node):
    for child in function_node.children:
        if child.type == "name":
            return child.value

def find_mutants(node):
    global current_func

    for child in node.children:
        if child.type == "funcdef":
            current_func = child
            find_mutants_rec(child)
            current_func = None

def relative_positions(start, end, func):
    start_pos = (start[0] - func.start_pos[0], start[1] - func.start_pos[1])
    end_pos = (end[0] - func.start_pos[0], end[1] - func.start_pos[1])
    return (start_pos, end_pos)


def find_mutants_rec(node):
    global all_mutants
    global current_func

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
        elif child.type == "return_stmt":
            start_pos, end_pos = relative_positions(child.start_pos, child.end_pos, current_func)
            new_str = "pass"
            find_mutants_rec(child)

        if start_pos is not None:
            str_mutant = StrMutant(current_func_name, start_pos, end_pos, new_str)
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

def write_to_mutation_file(output_file, func_code, mutant, index):
    file = open(output_file.name, "a")

    file.write("@mg.mutant_of(\"" + mutant.func_name + "\", \"" + mutant.func_name.upper() + "_" + str(index) + "\")\n")
    start = mutant.start_pos
    end = mutant.end_pos

    for i, line in enumerate(func_code):
        if i == 0:
            file.write("def" + line[3:].replace(mutant.func_name, mutant.func_name + "_" + str(index), 1) + "\n")
        elif i == start[0]:
            file.write(line[:start[1]] + mutant.new_str + line[end[1]:] + "\n")
        else:
            file.write(line + "\n")

    file.close()

def make_valid_import(file, module):
    assert file[-3:] == ".py"

    return path.join(path.basename(module), path.relpath(file, start=module)).replace("/", ".")[:-3]

def main():
    global all_mutants

    parser = argparse.ArgumentParser(description="Suggest mutants to the user that can keep them or delete them.\n\
                                        The kept mutants are written to a file and ready to use with pytest-mutagen")
    parser.add_argument('input_file', type=argparse.FileType('r'),
                        help='path to the file(s) to mutate')
    parser.add_argument('-o', '--output-file', default="mutations.py", type=argparse.FileType('w'),
                        help='path to the file where the sum should be written')
    parser.add_argument('-m', '--module-path', default=None,
                        help='path to the module directory (location of __init__.py) for import purposes')
    args = parser.parse_args()
    input_file = args.input_file
    output_file = args.output_file
    module_path = args.module_path if args.module_path else path.dirname(input_file.name)
    content = input_file.read()
    input_file.close()

    tree = parso.parse(content)
    find_mutants(tree)

    output_file.write("import pytest_mutagen as mg\n")
    output_file.write("import " + path.basename(module_path) + "\n")
    output_file.write("from " + make_valid_import(input_file.name, module_path) + " import ")
    for i, func_name in enumerate(all_mutants.keys()):
        output_file.write(func_name + (", " if i < len(all_mutants) - 1 else ""))
    output_file.write("\n\n")
    output_file.write("mg.link_to_file(mg.APPLY_TO_ALL)\n\n")
    output_file.close()


    for child in tree.children:
        if child.type == "funcdef":
            func_code = child.get_code().split("\n")
            func_name = get_func_name(child)
            empty_lines = 0

            for line in func_code:
                if line == "":
                    empty_lines += 1
                else:
                    break
            func_code = func_code[empty_lines:]

            for i, mutant in enumerate(all_mutants.get(func_name, [])):
                title = "# Function " + func_name + " #"

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
                    write_to_mutation_file(output_file, func_code, mutant, i)

if __name__=="__main__":
    main()