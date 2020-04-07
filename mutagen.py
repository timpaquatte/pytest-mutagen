from hypothesis import given, strategies as st

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

    def apply_and_run(self, f):
        global g_current_mutant
        g_current_mutant = self
        result = True

        saved = {}
        for (fname, fimpl) in self.function_mappings.items():  # mutate
            if fname in globals():
                saved[fname] = globals()[fname]
            globals()[fname] = fimpl

        try:
            f()  # run the function
        except Exception:
            result = False

        for (fname, fimpl) in saved.items():  # fix locals
            globals()[fname] = fimpl

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


def mutagen(suite):
    for mutant in g_mutants:
        assert mutant.apply_and_run(suite) is False, \
            "Test suite passed!\n" + mutant.name + ": " + mutant.description


# Example


def inc(x):
    return x + 1


def merge_sort(arr):
    if len(arr) > 1:
        mid = len(arr) // 2
        left = arr[:mid]
        right = arr[mid:]

        merge_sort(left)
        merge_sort(right)

        i = j = k = 0

        while i < len(left) and j < len(right):
            if mut("FLIP_LT", lambda: left[i] < right[j],
                   lambda: left[i] > right[j]):
                arr[k] = left[i]
                i = inc(i)
            else:
                arr[k] = right[j]
                j = inc(j)
            k = inc(k)

        while i < len(left):
            arr[k] = left[i]
            i = inc(i)
            k = inc(k)

        while j < len(right):
            arr[k] = mut("DUP_LEFT", lambda: right[j], lambda: left[i])
            j = inc(j)
            k = inc(k)


# Test Suite


@given(st.lists(st.integers()))
def test1(arr1):
    arr2 = arr1.copy()

    arr1.sort()
    merge_sort(arr2)

    assert arr1 == arr2


@given(st.lists(st.integers()))
def test2(arr):
    arr.sort()

    assert all([arr[k] <= arr[k + 1] for k in range(len(arr) - 1)])


def suite():
    test1()
    test2()


# Mutation Test Harness

declare_mutants({
    "INC_OBO": "Increment is off by one (increments by 2).",
    "FLIP_LT": "Flip a less-than check.",
    "DUP_LEFT": "Duplicate the left side of the list when merging."
})


@mutant_of("inc", "INC_OBO")
def inc_mut(x):
    return x + 2


def test_mutation():
    mutagen(suite)
