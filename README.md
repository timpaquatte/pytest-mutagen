# Mutagen
Mutagen is a mutation-testing module designed to be used in parallel with Hypothesis. It allows you to manually define mutant versions of your functions/expressions in order to check that your test suite catches the mistakes.

# Installation
* Clone this repository
* Find the folder on your system that contains python libraries :
	```
	python3 -c "import sys; print(sys.path)"
	```
* Create in this folder a symbolic link to the hypothesis-mutagen repository previously cloned :
	```
	ln -s hypothesis_mutagen /path/to/hypothesis-mutagen
	```
* Install it with pip
	```
	python3 -m pip install -e /path/to/symbolic/link/hypothesis_mutagen
	```
# Usage
## Python import
`from hypothesis_mutagen import pytest_mutagen as mg`

## Declare a mutant
* Mutant function
	To mutate a whole function you firstly have to declare it mutable with the `@mg.mutable` decorator. Then you have to write the new version of the function, decorated with `@mg.mutant_of(function_name, mutant_name, description (optional))`.
	Example :

	```python
	@mg.mutable
	def  inc(x):
		return x + 1

	@mg.mutant_of("inc", "INC_OBO", description="Increment is off by one.")
	def  inc_mut(x):
		return x + 2
	```

* Mutant expression
	If you don't want to change the whole function but only one line, you must decorate the function with `@mg.has_mutant(mutant_name, description (optional))`, then you have two ways to do it :
  
  * By replacing the expression by the `mg.mut(mutant_name, normal_expression, mutant_expression)` function, using lambda expressions.
			Example :
			`mg.mut("FLIP_LT", lambda: a < b, lambda: b < a)`

  * Using the `mg.not_mutant(mutant_name)` function combined with an `if` statement.
			Example :
			`k = inc(k) if mg.not_mutant("INC_OBO2") else inc(k) + 1`
  If you want to mutate several expressions in the same function you have to use one decorator per mutation.

### Mutating a class method

In fact the `@mutant_of` decorator doesn't require the function name but its fully qualified name. It does not change anything for top-level functions but in the case of a class method you need to write the dotted path leading to the object from the module top-level.
Example :
```python
class Foo:
	@mg.mutable
	def bar(self):
		pass
	
	@staticmethod
	@mg.mutable
	def static_bar():
		pass

@mg.mutant_of("Foo.bar", "")
def bar_mut(self):
	pass

@mg.mutant_of("Foo.static_bar", "")
def static_bar_mut():
	pass
```

:warning: **Mutating a static method**: Make sure that the `@staticmethod` decorator is above the `@mg.mutable` one

## Run the tests
`python3 -m pytest --mutate file_with_test_functions_and_mutations.py`

## Examples
* The file short_example.py is a very simple example of the use of mutagen to test a merge sort function
* The file BST_mutations.py implements the Binary Search Tree data structure, and the test suite and mutations from _How to specify it!_ (John Hughes, 2019)
