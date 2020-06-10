import pytest_mutagen as mg
from src import *

mg.link_to_file("test_file.py")

@mg.mutant_of("Toto.meth", "METH_5")
def Toto_mut(self, x):
    return 5

@mg.mutant_of("f", "F_O")
def f_mut(x):
    return 0
