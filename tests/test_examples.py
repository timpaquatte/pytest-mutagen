
def test_BST_mutations(testdir):
    testdir.copy_example("BST_mutations.py")
    result = testdir.runpytest("--mutate", "--collect-only", "--quick-mut")
    assert result.outlines[-2] == '[SUCCESS] BST_mutations.py: All mutants made at least one test fail'

def test_short_example(testdir):
    testdir.copy_example("short_example.py")
    result = testdir.runpytest("--mutate", "--collect-only", "--quick-mut", "short_example.py")
    assert result.outlines[-2] == "[ERROR]   short_example.py: The following mutants passed all tests: ['NO_MUTATION']"

def test_separate_files(testdir):
    testdir.copy_example("separate_files")
    result = testdir.runpytest("--mutate", "--collect-only", "--quick-mut")
    assert result.outlines[-2] == '[SUCCESS] test_file.py: All mutants made at least one test fail'