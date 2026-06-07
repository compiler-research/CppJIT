import py, os, sys
from pytest import raises, mark
from .support import setup_make

currpath = py.path.local(__file__).dirpath()
test_dct = str(currpath.join("example01Dict"))

def setup_module(mod):
    setup_make("example01")

class TestACLASSLOADER:

    def setup_class(cls):
        cls.test_dct = test_dct
        import cppyy
        cls.example01 = cppyy.load_reflection_info(cls.test_dct)

    def test01_class_autoloading(self):
        """Test whether a class can be found"""
        import cppyy
        example01_class = cppyy.gbl.example01
        assert example01_class
        cl2 = cppyy.gbl.example01
        assert cl2
        assert example01_class is cl2
