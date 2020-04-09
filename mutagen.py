# Global list of all mutants
g_mutant_registry = {}

# Current mutant (set by Mutant::apply_and_run)
g_current_mutant = None


class Mutant(object):
    def __init__(self, name, description):
        self.function_mappings = {}
        self.name = name
        self.description = description

    def add_mapping(self, fname, fimpl):
        self.function_mappings[fname] = fimpl

    def apply_and_run(self, f):
        global g_current_mutant
        g_current_mutant = self
        result = True
        try:
            f()
        except Exception:
            result = False
        g_current_mutant = None

        return result


def active_mutant(mutation):
    global g_current_mutant
    return g_current_mutant and \
        g_current_mutant.name == mutation


def mut(mutation, good, bad):
    global g_current_mutant

    if g_current_mutant and g_current_mutant.name == mutation:
        return bad()
    else:
        return good()


def mutant_of(fname, mutant_name):
    def decorator(f):
        global g_mutant_registry

        for m in g_mutant_registry.values():
            if m.name == mutant_name:
                m.add_mapping(fname, f)
                break
        else:
            m = Mutant(mutant_name, "")
            m.add_mapping(fname, f)
            g_mutant_registry[mutant_name] = m

        return f

    return decorator


def mutable(f):
    def inner(*args, **kwargs):
        global g_current_mutant

        if g_current_mutant and \
           f.__name__ in g_current_mutant.function_mappings:
            return g_current_mutant.function_mappings[f.__name__](*args,
                                                                  **kwargs)
        return f(*args, **kwargs)

    return inner


def mutagen(suite, mutants_to_run):
    global g_mutant_registry

    for mutant_name in mutants_to_run:
        m = g_mutant_registry[mutant_name] \
            if mutant_name in g_mutant_registry else Mutant(mutant_name, "")
        assert m.apply_and_run(suite) is False, \
            ("Test suite passed!\n" + m.name + ": " +
                m.description)
