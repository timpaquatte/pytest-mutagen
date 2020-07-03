# Mutagen

Mutagen is a plugin to pytest that makes it easy to do mutation testing. Mutation testing is a
method of testing your tests. Mutagen helps you to define "mutant" versions of your code---code
which is intentionally buggy---then you run your test suite on these mutants and verify that your
tests actually catch the bugs. Mutation testing helps you to gauge test coverage and verify that
your tests are good enough to exercise interesting behaviors in your code.

## For Property-Based Testing

If you are a user of a *property-based testing* framework such as Hypothesis, mutation testing can
also be used to test your input generators. It is relatively easy to write a generator that cannot
generate a certain kind of input. Mutation testing can be used to find those gaps.


# Installation

```
python3 -m pip install pytest-mutagen
```

# Usage
## Python import
`import pytest_mutagen as mg`

## Declare a mutant
* **Mutant function** \
	To mutate a whole function you have to write the new version of the function, decorated with `@mg.mutant_of(function_qual_name, mutant_name, file (optional), description (optional))`. If the mutations affect an object (function or class) you have to be sure that this object exists in the `__globals__` symbols table of the mutant functions. For this purpose you can simply write `from [your_module] import [target_object]` in the mutation file.
	Example :

	```python
	def  inc(x):
		return x + 1

	@mg.mutant_of("inc", "INC_OBO", description="Increment is off by one.")
	def  inc_mut(x):
		return x + 2
	```

* **Mutant expression** \
	If you don't want to change the whole function but only one line, you must decorate the function with `@mg.has_mutant(mutant_name, file (optional), description (optional))`. Then you have two ways to do it :

  * By replacing the expression by the `mg.mut(mutant_name, normal_expression, mutant_expression)` function, using lambda expressions. \
			Example :
			`mg.mut("FLIP_LT", lambda: a < b, lambda: b < a)`

  * Using the `mg.not_mutant(mutant_name)` function combined with an `if` statement. \
			Example :
			`k = inc(k) if mg.not_mutant("INC_OBO2") else inc(k) + 1`

### Mutating a class method

In fact the `@mutant_of` decorator doesn't require the function name but its fully qualified name. It does not change anything for top-level functions but in the case of a class method you need to write the dotted path leading to the object from the module top-level.
Example :
```python
class Foo:
	def bar(self):
		pass

	@staticmethod
	def static_bar():
		pass

@mg.mutant_of("Foo.bar", "")
def bar_mut(self):
	pass

@mg.mutant_of("Foo.static_bar", "")
def static_bar_mut():
	pass
```

## Global functioning

Mutagen collects all declared mutants, stored per file names. Then it looks through all tests collected by pytest and apply the mutants to the matching files. This is handled by the optional file parameter in `@has_mutant` and `@mutant_of` which can be a file name or a list of file names where you want your mutant to be applied. You can set it to APPLY_TO_ALL (constant string declared in mutagen) if you want it to be applied to all collected files. By default, file is :
* APPLY_TO_ALL for `@has_mutant`
* the current file name for `@mutant_of` (the one where it is written)

Therefore you can either :
* write your mutations and specify for each one where you want it to be applied (use the function `mg.link_to_file(filename)` at the beginning of your file to link the current file to the specified filename)
* or create a mutations.py file where you import all test files you want (`from testfile.py import *`), write your `mutant_of` with no file specified and run pytest on mutation.py.

## Run the tests

`python3 -m pytest --mutate`

### Quick run

The `--quick-mut` option will stop each mutant after its first failed test. If not specified each mutant will run the whole test suite

### Cache use

Mutagen stores in the pytest cache the functions that failed during the last run, for each mutant. For the next runs it will try these functions first, in order to find failures more quickly. If you don't need this feature you can simply use the `--cache-clear` option that will clear the cache before running the tests.

### Run only the mutations

If you don't want to run the original test suite but only the mutations you can use the pytest option `--collect-only`

### Selective run of mutants

The `--select` option expects a comma-separated list of mutants (no spaces) and will run these ones exclusively.  
Example :
```sh
python3 -m pytest --mutate --select INC_OBO,FLIP_LT
```

### Mutagen stats

The `--mutagen-stats` option adds a section to the terminal summary, which displays the number of tests that caught each mutant.

## Add trivial mutations

To find holes in a test suite with mutagen, we often try trivial mutations on some functions (like 
replacing them with pass) to see whether a lot of tests catch them or not. 
For this purpose the `trivial_mutations(functions, obj=None, file=APPLY_TO_ALL)` function with a 
list of functions as input adds all mutants corresponding to replacing them by an empty function.
There are two ways to use it :

```python
from module import sort, invert, ExampleClass

# With a list of top-level functions
mg.trivial_mutations([sort, invert])

# With a list of method names and the corresponding object
mg.trivial_mutations(["sort", "clear"], ExampleClass)

```

This is equivalent to doing this:

```python
from module import sort, invert, ExampleClass

mg.link_to_file(mg.APPLY_TO_ALL)

@mg.mutant_of("sort", "SORT_NOTHING")
def sort_mut(*args, **kwargs):
	pass

@mg.mutant_of("invert", "INVERT_NOTHING")
def invert_mut(*args, **kwargs):
	pass

@mg.mutant_of("ExampleClass.sort", "EXAMPLECLASS.SORT_NOTHING")
def sort_mut(*args, **kwargs):
	pass

@mg.mutant_of("ExampleClass.clear", "EXAMPLECLASS.CLEAR_NOTHING")
def clear_mut(*args, **kwargs):
	pass
```

`trivial_mutations` has an optional _file_ parameter to specify the test file where the mutations 
should be applied, which is by default set to APPLY_TO_ALL.  

The function `trivial_mutations_all(object, file=APPLY_TO_ALL)` applies this process to each
method of the class (or list of classes) given as a parameter.  
Example:

```python
from module import ExampleClass

mg.trivial_mutations_all(ExampleClass)
```

## Examples
You can find some examples in the examples folder
* The file short_example.py is a very simple example of the use of mutagen to test a merge sort function
* The file BST_mutations.py implements the Binary Search Tree data structure, and the test suite and mutations from _How to specify it!_ (John Hughes, 2019)
* The subfolder separate_files is an example of the separation between the source file, the test file and the mutation file


The run-tests.py scripts show how to run these tests
