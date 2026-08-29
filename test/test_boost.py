import os

from pytest import mark, raises, skip
from support import IS_MAC_ARM, IS_MAC_X86

noboost = False
if not (
    os.path.exists(os.path.join(os.path.sep, "usr", "include", "boost"))
    or os.path.exists(os.path.join(os.path.sep, "usr", "local", "include", "boost"))
):
    noboost = True


@mark.skipif(noboost == True, reason="boost not found")
class TestBOOSTANY:
    def setup_class(cls):
        import cppjit

        cppjit.include("boost/any.hpp")

    @mark.skipif((IS_MAC_ARM or IS_MAC_X86), reason="Fails to include boost on OS X")
    def test01_any_class(self):
        """Availability of boost::any"""

        import cppjit

        assert cppjit.gbl.boost.any

        from cppjit.gbl import std
        from cppjit.gbl.boost import any

        assert std.list[any]

    @mark.xfail(run=False, reason="boost::any casting crashes")
    def test02_any_usage(self):
        """boost::any assignment and casting"""

        import cppjit

        assert cppjit.gbl.boost

        from cppjit.gbl import boost, std

        val = boost.any()
        # test both by-ref and by rvalue
        v = std.vector[int]()
        val.__assign__(v)
        val.__assign__(std.move(std.vector[int](range(100))))
        assert val.type() == cppjit.typeid(std.vector[int])

        extract = boost.any_cast[std.vector[int]](val)
        assert type(extract) is std.vector[int]
        assert len(extract) == 100
        extract += range(100)
        assert len(extract) == 200

        val.__assign__(std.move(extract))  # move forced
        # assert len(extract) == 0      # not guaranteed by the standard

        # TODO: we hit boost::any_cast<int>(boost::any* operand) instead
        # of the reference version which raises
        boost.any_cast.__useffi__ = False
        try:
            # raises(Exception, boost.any_cast[int], val)
            assert not boost.any_cast[int](val)
        except Exception:
            # getting here is good, too ...
            pass

        extract = boost.any_cast[std.vector[int]](val)
        assert len(extract) == 200


@mark.skipif(((noboost == True) or IS_MAC_ARM or IS_MAC_X86), reason="boost not found")
class TestBOOSTOPERATORS:
    def setup_class(cls):
        import cppjit

        cppjit.include("boost/operators.hpp")

    def test01_ordered(self):
        """ordered_field_operators as base used to crash"""

        import cppjit

        try:
            cppjit.include("gmpxx.h")
        except ImportError:
            skip("gmpxx not installed")
        cppjit.cppdef("""
            namespace boost_test {
               class Derived : boost::ordered_field_operators<Derived>, boost::ordered_field_operators<Derived, mpq_class> {};
            }
        """)

        assert cppjit.gbl.boost_test.Derived


@mark.skipif(noboost == True, reason="boost not found")
class TestBOOSTVARIANT:
    def setup_class(cls):
        import cppjit

        cppjit.include("boost/variant/variant.hpp")
        cppjit.include("boost/variant/get.hpp")

    @mark.xfail(run=False, reason="boost::variant access crashes")
    def test01_variant_usage(self):
        """boost::variant usage"""

        # as posted on stackoverflow as example
        import cppjit

        cpp = cppjit.gbl
        std = cpp.std
        boost = cpp.boost

        cppjit.cppdef("""namespace BV {
          class A { };
          class B { };
          class C { }; } """)

        VariantType = boost.variant["BV::A, BV::B, BV::C"]
        VariantTypeList = std.vector[VariantType]

        v = VariantTypeList()

        v.push_back(VariantType(cpp.BV.A()))
        assert v.back().which() == 0
        v.push_back(VariantType(cpp.BV.B()))
        assert v.back().which() == 1
        v.push_back(VariantType(cpp.BV.C()))
        assert v.back().which() == 2

        assert type(boost.get["BV::A"](v[0])) == cpp.BV.A

        # Trying to raise this exception seg faults, by trying to execute an unfit instantiation.
        # This comes from `Instantiate` obtaining a single handle and providing a result
        # The same issue happens with trying `BestOverloadFunctionMatch` first since the candidate set is single
        raises(Exception, boost.get["BV::B"], v[0])
        assert type(boost.get["BV::B"](v[1])) == cpp.BV.B
        assert type(boost.get["BV::C"](v[2])) == cpp.BV.C


@mark.skipif(((noboost == True) or IS_MAC_ARM or IS_MAC_X86), reason="boost not found")
class TestBOOSTERASURE:
    def setup_class(cls):
        import cppjit

        cppjit.include("boost/type_erasure/any.hpp")
        cppjit.include("boost/type_erasure/member.hpp")
        cppjit.include("boost/mpl/vector.hpp")

    def test01_erasure_usage(self):
        """boost::type_erasure usage"""

        import cppjit

        cppjit.cppdef("""
            BOOST_TYPE_ERASURE_MEMBER((has_member_f), f, 0)

            using LengthsInterface = boost::mpl::vector<
                boost::type_erasure::copy_constructible<>,
                has_member_f<std::vector<int>() const>>;

            using Lengths = boost::type_erasure::any<LengthsInterface>;

            struct Unerased {
                std::vector<int> f() const { return std::vector<int>{}; }
            };

            Lengths lengths() {
                return Unerased{};
            }
        """)

        assert cppjit.gbl.lengths() is not None
