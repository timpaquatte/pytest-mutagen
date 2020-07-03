from os import path
import inspect


APPLY_TO_ALL = "**all**"

# Global list of all mutants
g_mutant_registry = {APPLY_TO_ALL:{}}

# Current mutant
g_current_mutant = None

linked_files = {}

class Mutant(object):
    def __init__(self, name, description):
        self.function_mappings = {}
        self.name = name
        self.description = description
        self.nb_catches = 0

    def add_mapping(self, fname, fimpl):
        self.function_mappings[fname] = fimpl


def active_mutant(mutation):
    global g_current_mutant
    return g_current_mutant and \
        g_current_mutant.name == mutation


def not_mutant(mutation):
    return not active_mutant(mutation)


def mut(mutation, good, bad):
    global g_current_mutant

    if g_current_mutant and g_current_mutant.name == mutation:
        return bad()
    else:
        return good()

def check_linked_files(file, default_value):
    file = file if not file is None else default_value
    files = []
    if isinstance(file, str):
        files = [linked_files[file]] if file in linked_files else [file]
    elif isinstance(file, list):
        for f in file:
            files.append(linked_files[f] if f in linked_files else f)
    else:
        raise ValueError("file must be a string or a list of strings")
    return files


def mutant_of(fname, mutant_name, file=None, description=""):

    def decorator(f):
        files = check_linked_files(file, path.basename(inspect.stack()[1].filename))

        has_mutant(mutant_name, files, "")(f)

        for filename in files:
            g_mutant_registry[filename][mutant_name].add_mapping(fname, f)

        return f

    return decorator

def has_mutant(mutant_name, file=None, description=""):

    def decorator(f):
        files = check_linked_files(file, APPLY_TO_ALL)

        for basename in files:
            if basename not in g_mutant_registry:
                g_mutant_registry[basename]=  {}

            if mutant_name not in g_mutant_registry[basename]:
                g_mutant_registry[basename][mutant_name] = Mutant(mutant_name, description)
        return f

    return decorator

def link_to_file(filename):
    global linked_files

    current_file = path.basename(inspect.stack()[1].filename)
    linked_files[current_file] = filename

def empty_function(*args, **kwargs):
    pass

def trivial_mutations(functions, obj=None, file=APPLY_TO_ALL):
    if not isinstance(functions, list):
        functions = [functions]
    if not obj is None:
        empty_function.__globals__[obj.__name__] = obj
    for func in functions:
        fname = (obj.__name__ + "." + func) if not obj is None else func.__name__
        if callable(func):
            empty_function.__globals__[fname] = func
        mutant_of(fname, fname.upper() + "_NOTHING", file=file)(empty_function)

def trivial_mutations_all(objects, file=APPLY_TO_ALL):
    if not isinstance(objects, list):
        objects = [objects]
    for obj in objects:
        functions_to_mutate = []
        for name, member in obj.__dict__.items():
            if inspect.isfunction(member):
                functions_to_mutate.append(name)
        trivial_mutations(functions_to_mutate, obj, file)

def reset_globals():
    global g_mutant_registry
    global linked_files
    global g_current_mutant

    linked_files.clear()
    for file, mutants in g_mutant_registry.items():
        for name, mutant in mutants.items():
            del mutant
    g_mutant_registry = {APPLY_TO_ALL:{}}
    g_current_mutant = None