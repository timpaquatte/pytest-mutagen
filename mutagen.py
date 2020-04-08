# Global list of all mutants
g_mutants = []

# Current mutant (set by Mutant::apply_and_run)
g_current_mutant = None


class Mutant(object):
    def __init__(self, name, description):
        self.function_mappings = {}
        self.name = name
        self.description = description

    def add_mapping(self, fname, fimpl):
        self.function_mappings[fname] = fimpl

    def apply_and_run(self, f, tests_globals):
        global g_current_mutant
        g_current_mutant = self
        result = True

        saved = {}
        for (fname, fimpl) in self.function_mappings.items():  # mutate
            if fname in tests_globals:
                saved[fname] = tests_globals[fname]
            tests_globals[fname] = fimpl

        try:
            f()  # run the function
        except Exception:
            result = False

        for (fname, fimpl) in saved.items():  # fix locals
            tests_globals[fname] = fimpl

        g_current_mutant = None

        return result


def mut(mutation, good, bad):
    global g_current_mutant

    if g_current_mutant and g_current_mutant.name == mutation:
        return bad()
    else:
        return good()


def declare_mutants(decls):
    global g_mutants

    for (name, description) in decls.items():
        g_mutants.append(Mutant(name, description))


def mutant_of(fname, mutant):
    global g_mutants

    for m in g_mutants:
        if m.name == mutant:

            def inner(f):
                m.add_mapping(fname, f)
                return f

            return inner
    else:
        raise Exception("Undeclared mutant: " + mutant)


def mutagen(suite, tests_globals):
    for mutant in g_mutants:
        assert mutant.apply_and_run(suite, tests_globals) is False, \
            "Test suite passed!\n" + mutant.name + ": " + mutant.description
