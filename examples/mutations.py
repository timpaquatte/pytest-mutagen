from hypothesis_mutagen import pytest_mutagen as mg

from testfile import *

@mg.mutant_of("Toto.meth", "METH_5")
def Toto_mut(self, x):
    return 5

@mg.mutant_of("f", "F_O")
def f_mut(x):
    return 0
