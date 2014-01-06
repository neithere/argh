from argh.compat import _PrimitiveOrderedDict


def test_ordered_dict():
    d = _PrimitiveOrderedDict()
    d['a'] = 1
    d['b'] = 2
    d['c'] = 3
    assert list(d) == ['a', 'b', 'c']
    assert d.keys() == ['a', 'b', 'c']
    assert d.values() == [1, 2, 3]
    del d['b']
    assert list(d) == ['a', 'c']
