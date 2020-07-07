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
    ''' Return True if the current active mutant is mutation, else False '''
    global g_current_mutant
    return g_current_mutant and \
        g_current_mutant.name == mutation


def not_mutant(mutation):
    ''' Return False if the current active mutant is mutation, else True '''
    return not active_mutant(mutation)


def mut(mutation, good, bad):
    '''
    Execute and return the result of an expression depending on the current active mutant

    Inputs:
        * mutation [string] represents a mutant name
        * good [lambda expression] corresponds to the normal behavior
        * bad [lambda expression] corresponds to the mutated behavior
    '''
    global g_current_mutant

    if g_current_mutant and g_current_mutant.name == mutation:
        return bad()
    else:
        return good()

def check_linked_files(file, default_value):
    '''
    Replace each file in the list with its eventual linked file

    Inputs:
        * file [string | list] file name(s)
        * default_value [string] value used if file is None
    '''
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
    '''
    Decorator that registers the function to which it is applied as a mutant version of the
    function fname

    Inputs:
        * fname [string] is the name of the function that will be mutated
        * mutant_name [string] is the name of this mutant
        * file [string] is the name of the test file where the mutation will be applied
        * description [string] is the optional description of the mutant
    '''
    def decorator(f):
        files = check_linked_files(file, path.basename(inspect.stack()[1].filename))

        has_mutant(mutant_name, files, "")(f)

        for filename in files:
            g_mutant_registry[filename][mutant_name].add_mapping(fname, f)

        return f

    return decorator

def has_mutant(mutant_name, file=None, description=""):
    '''
    Decorator that registers the function to which it is applied as an inline mutant

    Inputs:
        * mutant_name [string] is the name of this mutant
        * file [string] is the name of the test file where the mutation will be applied
        * description [string] is the optional description of the mutant
    '''
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
    '''
    Link the file where it is written to filename

    Input: filename [string]
    '''
    global linked_files

    current_file = path.basename(inspect.stack()[1].filename)
    linked_files[current_file] = filename

def empty_function(*args, **kwargs):
    ''' This function is used as a mutant function in trivial_mutations '''
    pass

def trivial_mutations(functions, obj=None, file=APPLY_TO_ALL):
    '''
    Automatically register mutants where the empty function will replace the functions given as
    parameter

    Inputs:
        * functions [string | function | list] are the functions to be mutated if obj is None, and
            the names of the methods of obj to be mutated is obj is not None
        * obj [class] is the class where the methods to mutate are (by default None for top-level
            functions)
        * file [string | list] the file(s) where the mutations will be applied (by default applied
            to all files)
    '''
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
    '''
    Automatically register mutants where the empty function will replace all the methods of the
    object(s) given as parameter

    Inputs:
        * obj [class | list] is the class where the methods to mutate are (can be a list of classes)
        * file [string | list] the file(s) where the mutations will be applied (by default applied
            to all files)
    '''
    if not isinstance(objects, list):
        objects = [objects]
    for obj in objects:
        functions_to_mutate = []
        for name, member in obj.__dict__.items():
            if inspect.isfunction(member):
                functions_to_mutate.append(name)
        trivial_mutations(functions_to_mutate, obj, file)

def reset_globals():
    ''' Reset all declared global variables '''
    global g_mutant_registry
    global linked_files
    global g_current_mutant

    linked_files.clear()
    for file, mutants in g_mutant_registry.items():
        for name, mutant in mutants.items():
            del mutant
    g_mutant_registry = {APPLY_TO_ALL:{}}
    g_current_mutant = None