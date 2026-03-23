import cppyy
from pytest import raises

cppyy.cppdef('#define HELLO "Hello, World!"')
assert cppyy.macro("HELLO") == "Hello, World!"

with raises(ValueError):
    cppyy.macro("SOME_INT")

cppyy.cppdef('#define SOME_INT 42')
assert cppyy.macro("SOME_INT") == 42