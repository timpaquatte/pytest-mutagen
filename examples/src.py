
class Base():
    def __init__(self):
        pass

class Toto(Base):
    def meth(self, x):
        return x**2 + 1

def f(x):
    return x + 1