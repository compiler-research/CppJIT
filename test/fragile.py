import cppyy, py

currpath = py.path.local(__file__).dirpath()
test_dct = str(currpath.join("fragileDict"))

cppyy.load_reflection_info(test_dct)

assert cppyy.gbl.fragile == cppyy.gbl.fragile
fragile = cppyy.gbl.fragile

d = fragile.D()
try:
    d.check(None)         # raises TypeError
    assert 0
except TypeError as e:
    assert "fragile::D::check()" in str(e)
    assert "TypeError: takes at most 0 arguments (1 given)" in str(e)
    assert "TypeError: takes at least 2 arguments (1 given)" in str(e)

try:
    d.overload(None)      # raises TypeError
    assert 0
except TypeError as e:
    # TODO: pypy-c does not indicate which argument failed to convert, CPython does
    # likewise there are still minor differences in descriptiveness of messages
    err_msg = str(e).replace(" ", "")
    assert "fragile::D::overload()" in err_msg
    assert "TypeError: takes at most 0 arguments (1 given)" in str(e)
    assert "fragile::D::overload(fragile::no_such_class*)" in err_msg
    #assert "no converter available for 'fragile::no_such_class*'" in str(e)
    assert "void fragile::D::overload(char, int i = 0)".replace(" ", "") in err_msg
    #assert "char or small int type expected" in str(e)
    assert "void fragile::D::overload(int, fragile::no_such_class * p = 0)".replace(" ", "") in err_msg
    #assert "int/long conversion expects an integer object" in str(e)