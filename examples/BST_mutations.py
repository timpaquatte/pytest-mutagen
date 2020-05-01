from hypothesis import given, strategies as st, control
import sys
import random as rd
import pytest_mutagen as mg

######################################
#  DEFINITION AND OPERATIONS OF BST  #
######################################


def isLeaf(t):
    return t.data is None and t.left is None and t.right is None


def isNode(t):
    return t.data is not None and t.left is not None and t.right is not None


class BST:
    def __init__(self, d=None, lt=None, r=None):
        self.left = lt
        self.right = r
        self.data = d

        if (not isLeaf(self)) and (not isNode(self)):
            sys.exit("Invalid BST")

    def __str__(self):
        if isLeaf(self):
            return "Leaf"
        elif isNode(self):
            return "Node " + str(self.data) + " (" + str(
                self.left) + ") (" + str(self.right) + ")"
        else:
            sys.exit("Malformed BST : " + str(self.data) + " (" +
                     str(self.left) + ") (" + str(self.right) + ")")


def max(t):
    if isLeaf(t):
        return None
    else:
        if isLeaf(t.right):
            return t.data
        else:
            return max(t.right)


def toList(t):
    if t is None or isLeaf(t):
        return []
    else:
        return toList(t.left) + [t.data] + toList(t.right)


def keys(t):
    return [x[0] for x in toList(t)]


def isBST(t):
    if t is None:
        return False
    if isLeaf(t):
        return True
    return (all([x < t.data[0] for x in keys(t.left)])) and \
        (all([x > t.data[0] for x in keys(t.right)])) and \
        isBST(t.left) and isBST(t.right)


def eq(t1, t2):
    if isLeaf(t1):
        return isLeaf(t2)
    if isLeaf(t2):
        return False
    if t1.data != t2.data:
        return False
    return eq(t1.left, t2.left) and eq(t1.right, t2.right)


def eqWeak(t1, t2):
    return toList(t1) == toList(t2)


def find(x, t):
    if t is None or isLeaf(t):
        return None

    k, v = t.data
    if x == k:
        return v
    elif x < k:
        return find(x, t.left)
    else:
        return find(x, t.right)


@mg.has_mutant("INSERT_NOUPDATE", file="BST_mutations.py")
def insert(x, t):
    if t is None or isLeaf(t):
        return BST(x, BST(), BST())

    k, v = t.data
    if x[0] == k:
        ret = mg.mut("INSERT_NOUPDATE", lambda: BST(x, t.left, t.right),
                     lambda: t)
        return ret
    elif x[0] < k:
        return BST(t.data, insert(x, t.left), t.right)
    else:
        return BST(t.data, t.left, insert(x, t.right))


@mg.has_mutant("DELETE_REMAINDER", file="BST_mutations.py")
def delete(x, t):
    if t is None or isLeaf(t):
        return t

    k, v = t.data
    if x < k:
        ret = mg.mut("DELETE_REMAINDER",
                     lambda: BST(t.data, delete(x, t.left), t.right),
                     lambda: delete(x, t.left))
        return ret
    elif x > k:
        ret = mg.mut("DELETE_REMAINDER",
                     lambda: BST(t.data, t.left, delete(x, t.right)),
                     lambda: delete(x, t.right))
        return ret
    else:
        if isLeaf(t.left):
            return t.right
        elif isLeaf(t.right):
            return t.left
        else:
            m = max(t.left)
            return BST(m, delete(m[0], t.left), t.right)


def union(t1, t2):
    lst = toList(t1)
    if lst == []:
        return t2
    else:
        t = insert(lst[0], t2)
        for k in range(1, len(lst)):
            t = insert(lst[k], t)
        return t


def listToBST(l):
    t = BST()
    for k in l:
        t = insert(k, t)
    return t


def genBST():
    return st.builds(listToBST,
                     st.lists(st.tuples(st.integers(), st.integers())))


###########
#  TESTS  #
###########

# Validity properties


@given(genBST())
def test_valid(t):
    assert isBST(t)


@given(st.integers(), st.integers(), genBST())
def test_insertValid(k, v, t):
    assert isBST(insert((k, v), t))


@given(st.integers(), genBST())
def test_deleteValid(k, t):
    assert isBST(delete(k, t))


@given(genBST(), genBST())
def test_unionValid(t1, t2):
    assert isBST(union(t1, t2))


# Postconditions


@given(st.integers(), st.integers(), st.integers(), genBST())
def test_insertPost(k1, v, k2, t):
    x = find(k2, insert((k1, v), t))
    if k1 == k2:
        assert x == v
    else:
        assert x == find(k2, t)


@given(st.integers(), st.integers(), genBST())
def test_insertPostSameKey(k, v, t):
    assert find(k, insert((k, v), t)) == v


@given(st.integers(), st.integers(), genBST())
def test_deletePost(k1, k2, t):
    x = find(k2, delete(k1, t))
    if k1 == k2:
        assert x is None
    else:
        assert x == find(k2, t)


@given(st.integers(), genBST())
def test_deletePostSameKey(k, t):
    assert find(k, delete(k, t)) is None


@given(genBST(), genBST(), st.integers())
def test_unionPost(t1, t2, k):
    a = find(k, t1)
    b = find(k, t2)
    if a is None:
        assert find(k, union(t1, t2)) == b
    elif b is None:
        assert find(k, union(t1, t2)) == a
    else:
        assert find(k, union(t1, t2)) == a


@given(st.integers(), st.integers(), genBST())
def test_findPostPresent(k, v, t):
    assert find(k, insert((k, v), t)) == v


@given(st.integers(), genBST())
def test_findPostAbsent(k, t):
    assert find(k, delete(k, t)) is None


@given(st.integers(), genBST())
def test_insertDeleteComplete(k, t):
    f = find(k, t)
    if f is None:
        assert eq(t, delete(k, t))
    else:
        assert eq(t, insert((k, f), t))


# Metamorphic properties


@given(st.integers(), st.integers(), st.integers(), st.integers(), genBST())
def test_insertInsert(k1, v1, k2, v2, t):
    t2 = insert((k1, v1), insert((k2, v2), t))
    if k1 != k2:
        assert eqWeak(t2, insert((k2, v2), insert((k1, v1), t)))
    else:
        assert eqWeak(t2, insert((k1, v1), t))


@given(st.integers(), st.integers(), st.integers(), st.integers(), genBST())
def test_insertInsertWeak(k1, v1, k2, v2, t):
    control.assume(k1 != k2)
    assert eqWeak(insert((k1, v1), insert((k2, v2), t)),
                  insert((k2, v2), insert((k1, v1), t)))


@given(st.integers(), st.integers(), st.integers(), genBST())
def test_insertDelete(k1, v1, k2, t):
    t2 = insert((k1, v1), delete(k2, t))
    if k1 != k2:
        assert eqWeak(t2, delete(k2, insert((k1, v1), t)))
    else:
        assert eqWeak(t2, insert((k1, v1), t))


@given(st.integers(), st.integers(), genBST(), genBST())
def test_insertUnion(k, v, t1, t2):
    assert eqWeak(insert((k, v), union(t1, t2)), union(insert((k, v), t1), t2))


@given(st.integers(), st.integers(), st.integers(), genBST())
def test_deleteInsertWeak(k1, k2, v2, t):
    control.assume(k1 != k2)
    assert eqWeak(delete(k1, insert((k2, v2), t)),
                  insert((k2, v2), delete(k1, t)))


@given(st.integers(), st.integers(), st.integers(), genBST())
def test_deleteInsert(k1, k2, v2, t):
    t2 = delete(k1, insert((k2, v2), t))
    if k1 == k2:
        assert eqWeak(t2, delete(k1, t))
    else:
        assert eqWeak(t2, insert((k2, v2), delete(k1, t)))


@given(st.integers(), st.integers(), genBST())
def test_deleteDelete(k1, k2, t):
    assert eqWeak(delete(k1, delete(k2, t)), delete(k2, delete(k1, t)))


@given(st.integers(), genBST(), genBST())
def test_deleteUnion(k, t1, t2):
    assert eqWeak(delete(k, union(t1, t2)), union(delete(k, t1), delete(k,
                                                                        t2)))


@given(st.integers(), st.integers(), genBST(), genBST())
def test_unionDeleteInsert(k, v, t1, t2):
    assert eqWeak(union(delete(k, t1), insert((k, v), t2)),
                  insert((k, v), union(t1, t2)))


@given(genBST())
def test_unionUnionIdem(t):
    assert eqWeak(union(t, t), t)


@given(genBST(), genBST(), genBST())
def test_unionUnionAssoc(t1, t2, t3):
    assert eqWeak(union(t1, union(t2, t3)), union(union(t1, t2), t3))


@given(st.integers(), st.integers(), genBST(), genBST())
def test_findInsert(k1, k2, v2, t):
    f = find(k1, insert((k2, v2), t))
    if k1 == k2:
        assert f == v2
    else:
        assert f == find(k1, t)


@given(st.integers(), st.integers(), genBST())
def test_findDelete(k1, k2, t):
    f = find(k1, delete(k2, t))
    if k1 == k2:
        assert f is None
    else:
        assert f == find(k1, t)


@given(st.integers(), genBST(), genBST())
def test_findUnion(k, t1, t2):
    v = find(k, union(t1, t2))
    assert (v == find(k, t1)) or (v == find(k, t2))


# Preservation of equivalence


def listToEquivBST(xs):
    # Removing duplicate keys
    xs = list(dict(xs).items())

    a = listToBST(xs)
    rd.shuffle(xs)
    b = listToBST(xs)
    return a, b


def genEquivBST():
    return st.builds(listToEquivBST,
                     st.lists(st.tuples(st.integers(), st.integers())))


@given(st.integers(), st.integers(), genEquivBST())
def test_insertPreservesEquiv(k, v, p):
    t1, t2 = p
    assert eqWeak(insert((k, v), t1), insert((k, v), t2))


@given(st.integers(), genEquivBST())
def test_deletePreservesEquiv(k, p):
    t1, t2 = p
    assert eqWeak(delete(k, t1), delete(k, t2))


@given(genEquivBST(), genEquivBST())
def test_unionPreservesEquiv(p1, p2):
    t1, t2 = p1
    t3, t4 = p2
    assert eqWeak(union(t1, t3), union(t2, t4))


@given(st.integers(), genEquivBST())
def test_findPreservesEquiv(k, p):
    t1, t2 = p
    assert find(k, t1) == find(k, t2)


@given(genEquivBST())
def test_equivs(p):
    t1, t2 = p
    assert eqWeak(t1, t2)


# Inductive testing


@given(st.integers(), st.integers(), genBST(), genBST())
def test_unionInsert(k, v, t1, t2):
    assert eqWeak(union(insert((k, v), t1), t2), insert((k, v), union(t1, t2)))


def insertions(t):
    if isLeaf(t):
        return []
    return [t.data] + insertions(t.left) + insertions(t.right)


@given(genBST())
def test_insertComplete(t):
    assert eq(t, listToBST(insertions(t)))


@given(st.integers(), genBST())
def test_insertCompleteForDelete(k, t):
    t2 = delete(k, t)
    assert eq(t2, listToBST(insertions(t2)))


@given(genBST(), genBST())
def test_insertCompleteForUnion(t1, t2):
    t = union(t1, t2)
    assert eq(t, listToBST(insertions(t)))


# Model-based properties


def insertSortedList(x, xs):
    if xs == []:
        return [x]
    if x <= xs[0]:
        return [x] + xs
    return [xs[0]] + insertSortedList(x, xs[1:])


def deleteKey(k, xs):
    if xs == []:
        return []
    x, v = xs[0]
    if x == k:
        return deleteKey(k, xs[1:])
    return [xs[0]] + deleteKey(k, xs[1:])


def unionLists(l1, l2):
    if l1 == []:
        return l2
    if l2 == []:
        return l1
    if l1[0][0] < l2[0][0]:
        return [l1[0]] + unionLists(l1[1:], l2)
    elif l1[0][0] > l2[0][0]:
        return [l2[0]] + unionLists(l1, l2[1:])
    else:
        return [l1[0]] + unionLists(l1[1:], l2[1:])


@given(st.integers(), st.integers(), genBST())
def test_insertModel(k, v, t):
    assert toList(insert((k, v), t)) == insertSortedList(
        (k, v), deleteKey(k, toList(t)))


@given(st.integers(), genBST())
def test_deleteModel(k, t):
    assert toList(delete(k, t)) == deleteKey(k, toList(t))


@given(genBST(), genBST())
def test_unionModel(t1, t2):
    assert toList(union(t1, t2)) == sorted(unionLists(toList(t1), toList(t2)))


@given(st.integers(), genBST())
def test_findModel(k, t):
    assert find(k, t) == dict(toList(t)).get(k)


###############
#  MUTATIONS  #
###############


@mg.mutant_of("insert", "INSERT_ERASE")
def insert_bug1(x, t):
    return BST(x, BST(), BST())


@mg.mutant_of("insert", "INSERT_DUP")
def insert_bug2(x, t):
    if t is None or isLeaf(t):
        return BST(x, BST(), BST())

    k, v = t.data
    if x[0] < k:
        return BST(t.data, insert(x, t.left), t.right)
    else:
        return BST(t.data, t.left, insert(x, t.right))


@mg.mutant_of("delete", "DELETE_REV")
def delete_bug5(x, t):
    if t is None or isLeaf(t):
        return t

    k, v = t.data
    if x < k:
        return BST(t.data, t.left, delete(x, t.right))
    elif x > k:
        return BST(t.data, delete(x, t.left), t.right)
    else:
        if isLeaf(t.left):
            return t.right
        elif isLeaf(t.right):
            return t.left
        else:
            m = max(t.left)
            return BST(m, delete(m[0], t.left), t.right)


@mg.mutant_of("union", "UNION_FSTOVERSND")
def union_bug6(t1, t2):
    if isLeaf(t1):
        return t2
    m = max(t1)
    return BST(m, delete(m[0], t1), t2)


@mg.mutant_of("union", "UNION_ROOT")
def union_bug7(t1, t2):
    if isLeaf(t1):
        return t2
    if isLeaf(t2):
        return t1
    if t1.data < t2.data:
        m = max(t1)
        return BST(m, delete(m[0], t1), t2)
    else:
        m = max(t2)
        return BST(m, t1, delete(m[0], t2))


@mg.mutant_of("union", "UNION_OTHERPRIORITY")
def union_bug8(t1, t2):
    xs = toList(t1)
    if xs == []:
        return t2
    else:
        t = insert(xs[0], t2)
        for k in range(0, len(xs)):
            if find(xs[k], t2) is None:
                t = insert(xs[k], t)
        return t