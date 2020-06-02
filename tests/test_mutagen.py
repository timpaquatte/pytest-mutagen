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

################
# Actual tests #
################

# Test mutant_of

@given(WORD, WORD)
def test_mutant_of_with_file(mutant_name, file_name):
    mg.mutant_of("f", mutant_name, file=file_name)(empty_function)
    assert_mutant_registry_correct(mutant_name, file_name, True)
    mg.reset_globals()

@given(WORD)
def test_mutant_of_no_file(mutant_name):
    mg.mutant_of("f", mutant_name)(empty_function)
    assert_mutant_registry_correct(mutant_name, os.path.basename(__file__), True)
    mg.reset_globals()

@given(WORD, st.lists(WORD))
def test_mutant_of_several_files(mutant_name, files):
    mg.mutant_of("f", mutant_name, files)(empty_function)

    for file in files:
        assert_mutant_registry_correct(mutant_name, file, True)
    mg.reset_globals()

@given(WORD, WORD)
def test_mutant_of_linked_file(mutant_name, file_name):
    mg.link_to_file(file_name)
    mg.mutant_of("f", mutant_name)(empty_function)
    assert_mutant_registry_correct(mutant_name, file_name, True)
    mg.reset_globals()

@given(WORD, st.lists(WORD, min_size=1), WORD)
def test_mutant_of_several_linked_files(mutant_name, files, link_file):
    assume(not link_file in files)
    for file in files:
        mg.linked_files[file] = link_file

    mg.mutant_of("f", mutant_name, files)(empty_function)
    assert_mutant_registry_correct(mutant_name, link_file, True)

    for file in files:
        assert not file in mg.g_mutant_registry

    mg.reset_globals()

@given(WORD, st.integers())
def test_mutant_of_bad_type(name, number):
    with pytest.raises(ValueError):
        mg.mutant_of("f", name, file=number)(empty_function)

# Test has_mutant

@given(WORD, WORD)
def test_has_mutant_with_file(mutant_name, file):
    mg.has_mutant(mutant_name, file)(f)
    assert_mutant_registry_correct(mutant_name, file)
    mg.reset_globals()

@given(WORD)
def test_has_mutant_no_file(mutant_name):
    mg.has_mutant(mutant_name)(f)
    assert_mutant_registry_correct(mutant_name, mg.APPLY_TO_ALL)
    mg.reset_globals()

@given(WORD, st.lists(WORD))
def test_has_mutant_several_files(mutant_name, files):
    mg.has_mutant(mutant_name, files)(f)

    for file in files:
        assert_mutant_registry_correct(mutant_name, file)
    mg.reset_globals()

# Test trivial_mutations

@given(st.lists(WORD))
def test_trivial_mutations_list_only(func_list):
    mg.trivial_mutations(*func_list)
    for func in func_list:
        assert_mutant_registry_correct(func.upper() + "_NOTHING", os.path.basename(__file__))
    mg.reset_globals()

@given(st.lists(WORD), WORD)
def test_trivial_mutations_list_and_file(func_list, file):
    mg.trivial_mutations(*func_list, file=file)
    for func in func_list:
        assert_mutant_registry_correct(func.upper() + "_NOTHING", file)
    mg.reset_globals()

@given(st.lists(WORD))
def test_trivial_mutations_with_object(func_list):
    class ExampleClass:
        def __init__(self):
            pass

    mg.trivial_mutations(*list(map(lambda x: "ExampleClass." + x, func_list)), object=ExampleClass)
    current_file = os.path.basename(__file__)
    for func in func_list:
        mutant_name = func.upper() + "_NOTHING"
        assert_mutant_registry_correct(mutant_name, current_file)
        assert mg.g_mutant_registry[current_file][mutant_name].function_mappings["ExampleClass."+func] is mg.empty_function
        assert "ExampleClass" in mg.empty_function.__globals__
        assert mg.empty_function.__globals__["ExampleClass"] is ExampleClass
    mg.reset_globals()

# Test active_mutant

@given(WORD, WORD)
def test_active_mutant_correct(name, other_name):
    assume(name != other_name)
    mg.g_current_mutant = mg.Mutant(name, "")
    assert mg.active_mutant(name)
    assert mg.not_mutant(other_name)
    mg.reset_globals()

# Test mut

@given(WORD, WORD)
def test_mut_correct(name, other_name):
    assume(name != other_name)
    mg.g_current_mutant = mg.Mutant(name, "")
    assert mg.mut(name, lambda: False, lambda: True)
    assert mg.mut(other_name, lambda: True, lambda: False)
    mg.reset_globals()