import pytest_mutagen.mutagen as mg
from hypothesis import assume, given, strategies as st

import string
import os

import pytest

#########
# Tools #
#########

WORD = st.text(alphabet=string.ascii_letters, min_size=1)

def empty_function(*args, **kwargs):
    pass

def f(x):
    return x

def assert_mutant_registry_correct(mutant_name, file_name, with_function_mappings=False):
    assert file_name in mg.g_mutant_registry
    assert mutant_name in mg.g_mutant_registry[file_name]
    assert mg.g_mutant_registry[file_name][mutant_name].name == mutant_name
    assert mg.g_mutant_registry[file_name][mutant_name].description == ""

    if with_function_mappings:
        func_map = mg.g_mutant_registry[file_name][mutant_name].function_mappings
        assert "f" in func_map
        assert func_map["f"] is empty_function

def reset_globals():
    mg.linked_files.clear()
    for file, mutants in mg.g_mutant_registry.items():
        for name, mutant in mutants.items():
            del mutant
    mg.g_mutant_registry = {mg.APPLY_TO_ALL:{}}

################
# Actual tests #
################

@given(WORD, WORD)
def test_mutant_of_correct(mutant_name, file_name):
    mg.mutant_of("f", mutant_name, file=file_name)(empty_function)
    assert_mutant_registry_correct(mutant_name, file_name, True)
    reset_globals()

@given(WORD)
def test_mutant_of_no_file(mutant_name):
    mg.mutant_of("f", mutant_name)(empty_function)
    assert_mutant_registry_correct(mutant_name, os.path.basename(__file__), True)
    reset_globals()

@given(WORD, st.lists(WORD))
def test_mutant_of_several_files(mutant_name, files):
    mg.mutant_of("f", mutant_name, files)(empty_function)

    for file in files:
        assert_mutant_registry_correct(mutant_name, file, True)
    reset_globals()

@given(WORD, WORD)
def test_mutant_of_linked_file(mutant_name, file_name):
    mg.link_to_file(file_name)
    mg.mutant_of("f", mutant_name)(empty_function)
    assert_mutant_registry_correct(mutant_name, file_name, True)
    reset_globals()

@given(WORD, st.lists(WORD, min_size=1), WORD)
def test_mutant_of_several_linked_files(mutant_name, files, link_file):
    assume(not link_file in files)
    for file in files:
        mg.linked_files[file] = link_file

    mg.mutant_of("f", mutant_name, files)(empty_function)
    assert_mutant_registry_correct(mutant_name, link_file, True)

    for file in files:
        assert not file in mg.g_mutant_registry

    reset_globals()