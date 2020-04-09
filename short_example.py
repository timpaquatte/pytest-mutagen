from hypothesis import given, strategies as st
import mutagen as mg


@mg.mutable
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
            if mg.mut("FLIP_LT", lambda: left[i] < right[j],
                      lambda: left[i] > right[j]):
                arr[k] = left[i]
                i = inc(i)
            else:
                arr[k] = right[j]
                j = inc(j)
            k = inc(k)

        while i < len(left):
            arr[k] = left[i]
            if not mg.active_mutant("SKIP_BLOCK"):
                i = inc(i)
            k = inc(k)

        while j < len(right):
            arr[k] = mg.mut("DUP_LEFT", lambda: right[j], lambda: left[i])
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


@mg.mutant_of("inc", "INC_OBO")
def inc_mut(x):
    return x + 2


def test_mutation():
    mg.mutagen(suite, [
        "INC_OBO",
        "FLIP_LT",
        "DUP_LEFT",
        "SKIP_BLOCK"
    ])
