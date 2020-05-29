import pytest_mutagen.mutagen as mg

def empty_function(*args, **kwargs):
    pass

def f(x):
    return x

def test_mutant_of():
    mg.mutant_of("f", "F_NOTHING", file="file.py")(empty_function)
    assert "file.py" in mg.g_mutant_registry
    assert "F_NOTHING" in mg.g_mutant_registry["file.py"]
    assert mg.g_mutant_registry["file.py"]["F_NOTHING"].name == "F_NOTHING"
    assert mg.g_mutant_registry["file.py"]["F_NOTHING"].description == ""
    func_map = mg.g_mutant_registry["file.py"]["F_NOTHING"].function_mappings
    assert "f" in func_map
    assert func_map["f"] is empty_function