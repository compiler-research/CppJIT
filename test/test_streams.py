import py, os, sys
from pytest import raises, mark
from support import setup_make, IS_MAC, IS_CLANG_REPL

currpath = py.path.local(__file__).dirpath()
test_dct = str(currpath.join("std_streamsDict"))

def setup_module(mod):
    setup_make("std_streams")


class TestSTDStreams:
    def setup_class(cls):
        cls.test_dct = test_dct
        import cppyy
        cls.streams = cppyy.load_reflection_info(cls.test_dct)

    def test01_std_ostream(self):
        """Test availability of std::ostream"""

        import cppyy

        assert cppyy.gbl.std is cppyy.gbl.std
        assert cppyy.gbl.std.ostream is cppyy.gbl.std.ostream

        assert callable(cppyy.gbl.std.ostream)

    def test02_std_cout(self):
        """Test access to std::cout"""

        import cppyy

        assert not (cppyy.gbl.std.cout is None)

    @mark.xfail(condition=IS_MAC, reason="Fails on OS X")
    def test03_consistent_naming_if_char_traits(self):
        """Naming consistency if char_traits"""

        import cppyy

        cppyy.cppdef("""\
        namespace stringstream_base {
        void pass_through_base(std::ostream& o) {
            o << "TEST STRING";
        } }""")

        s = cppyy.gbl.std.ostringstream();
      # base class used to fail to match
        cppyy.gbl.stringstream_base.pass_through_base(s)
        assert s.str() == "TEST STRING"

    def test04_naming_of_ostringstream(self):
        """Naming consistency of ostringstream"""

        import cppyy

        # Check if the object created is equal in all three cases
        cl0 = cppyy.gbl.std.ostringstream
        cl1 = cppyy.gbl.std.basic_ostringstream['char']
        cl2 = cppyy.gbl.std.basic_ostringstream['char', cppyy.gbl.std.char_traits['char'] , cppyy.gbl.std.allocator['char']]

        assert cl0 == cl1
        assert cl1 == cl2
        assert cl2 == cl0

