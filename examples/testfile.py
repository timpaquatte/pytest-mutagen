from src import *

def test_Toto():
    t = Toto()
    assert t.meth(0) == 1
    assert t.meth(1) == 2
    assert t.meth(4) == 17

def test_f():
    assert f(0) == 1
    assert f(8) == 9