import pytest
import pytest_mutagen.mutagen as mg


@pytest.fixture(autouse=True)
def reset_globals():
    mg.reset_globals()

def verify_output(outlines, mutant_results, summary):
    for i, line in enumerate(outlines):
        if "= mutation session starts =" in line:
            break
    i += 2
    assert outlines[i:i+len(mutant_results)] == mutant_results

    for k in range(i, len(outlines)):
        if "= Mutagen =" in outlines[k]:
            i = k
            break
    i += 1
    assert outlines[i:i+len(summary)] == summary


def test_BST_mutations(testdir):
    testdir.copy_example("BST_mutations.py")
    result = testdir.runpytest("--mutate", "--collect-only", "--quick-mut", "BST_mutations.py")

    mutant_results = \
    []          # The exact result is non-deterministic in this case so we cannot compare precisely
    '''["Module BST_mutations.py:",
    "mmmmmM                                 	INSERT_NOUPDATE",
    "mmmmmmmmmmmM                           	DELETE_REMAINDER",
    "mmmmmmmmmmmmM                          	INSERT_ERASE",
    "M                                      	INSERT_DUP",
    "mmmmmmmmmmmmmmmmmM                     	DELETE_REV",
    "mmmM                                   	UNION_FSTOVERSND",
    "mmmM                                   	UNION_ROOT",
    "mmmM                                   	UNION_OTHERPRIORITY"]'''
    summary = \
    ["[SUCCESS] BST_mutations.py: All mutants made at least one test fail"]

    verify_output(result.outlines, mutant_results, summary)

def test_short_example(testdir):
    testdir.copy_example("short_example.py")
    result = testdir.runpytest("--mutate", "--collect-only", "--quick-mut", "short_example.py")

    mutant_results = \
    ["Module short_example.py:",
    "mm	NO_MUTATION	/!\ ALL TESTS PASSED",
    "M 	INC_OBO2",
    "M 	DUP_LEFT",
    "M 	SKIP_BLOCK",
    "M 	FLIP_LT",
    "M 	INC_OBO"]
    summary = \
    ["[ERROR]   short_example.py: The following mutants passed all tests: ['NO_MUTATION']"]

    verify_output(result.outlines, mutant_results, summary)


def test_separate_files(testdir):
    testdir.copy_example("separate_files")
    result = testdir.runpytest("--mutate", "--collect-only", "--quick-mut")

    mutant_results = \
    ["Module test_file.py:",
    "M 	METH_5",
    "mM	F_O"]
    summary = \
    ["[SUCCESS] test_file.py: All mutants made at least one test fail"]

    verify_output(result.outlines, mutant_results, summary)