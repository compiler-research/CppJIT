import os, sys, subprocess
from pytest import mark


# C++23 isn't the stack's default and the interpreter is a process-wide
# singleton pinned at the first `import cppyy`. So TestCPP23Driver re-runs the
# whole class once in a child process that selects C++23 before import
# (EXTRA_CLING_ARGS for cling, CPPINTEROP_EXTRA_INTERPRETER_ARGS for clang-repl);
# all tests then share that one interpreter. To iterate locally, run the tests
# directly in "child mode":
#
#     CPPYY_TEST_CPP23_CHILD=1 EXTRA_CLING_ARGS=-std=c++23 \
#     CPPINTEROP_EXTRA_INTERPRETER_ARGS=-std=c++23 \
#     pytest -v test_cpp23features.py

_CPP23_CHILD = "CPPYY_TEST_CPP23_CHILD"
_IN_CHILD = bool(os.environ.get(_CPP23_CHILD))


@mark.skipif(not _IN_CHILD,
             reason="C++23 tests run in the child interpreter launched by "
                    "TestCPP23Driver")
class TestCPP23FEATURES:
    """C++23 features driven via cppyy.cppdef through the JIT (clang-repl/cling).

    The class owns one C++23 interpreter (booted in setup_class); tests share
    it via ``self.cppyy``.
    """

    @classmethod
    def setup_class(cls):
        # In the child process C++23 is already selected, so this one-time boot
        # is the C++23 interpreter every test shares.
        import cppyy
        cls.cppyy = cppyy

    def test01_deducing_this_basic(self):
        """Explicit object parameter on a member function (P0847R7)"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct Widget {
            int value = 42;
            int get(this Widget& self) { return self.value; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.Widget()
        assert w.value == 42
        assert w.get() == 42

    def test02_deducing_this_const(self):
        """const explicit object parameter (this const Widget& self)"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct CWidget {
            int value = 7;
            int read(this const CWidget& self) { return self.value; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.CWidget()
        assert w.read() == 7

    def test03_deducing_this_by_value(self):
        """by-value explicit object parameter (this Widget self)"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct VWidget {
            int value = 5;
            int snapshot(this VWidget self) { return self.value; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.VWidget()
        w.value = 11
        assert w.snapshot() == 11

    def test04_deducing_this_with_extra_args(self):
        """explicit object parameter alongside regular arguments"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct AWidget {
            int base = 100;
            int add(this AWidget& self, int x, int y) { return self.base + x + y; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.AWidget()
        assert w.add(20, 3) == 123

    def test05_deducing_this_rvalue_ref(self):
        """rvalue-ref-qualified explicit object parameter (this Widget&&)"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct RWidget {
            int value = 13;
            int consume(this RWidget&& self) { return self.value; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.RWidget()
        assert w.consume() == 13

    def test05b_traditional_rvalue_ref_qualifier(self):
        """traditional rvalue-ref-qualified member (int f() &&), no deducing this"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct QWidget {
            int value = 17;
            int consume() && { return value; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.QWidget()
        assert w.consume() == 17

    def test06_deducing_this_chaining(self):
        """builder-style chaining: explicit object parameter returns self"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct BWidget {
            int value = 0;
            BWidget& set(this BWidget& self, int v) { self.value = v; return self; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.BWidget()
        r = w.set(5).set(8)
        assert r.value == 8
        assert w.value == 8           # same object returned by reference

    def test07_deducing_this_default_arg(self):
        """explicit object parameter with a defaulted regular argument"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct DWidget {
            int base = 3;
            int scale(this DWidget& self, int factor = 4) { return self.base * factor; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.DWidget()
        assert w.scale() == 12        # default factor=4
        assert w.scale(10) == 30

    def test08_deducing_this_call_operator(self):
        """call operator with an explicit object parameter"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct Adder {
            int base = 100;
            int operator()(this Adder& self, int x) { return self.base + x; }
        };
        }
        """)

        a = cppyy.gbl.Cpp23DeducingThis.Adder()
        assert a(23) == 123

    def test09_deducing_this_mixed_overload(self):
        """overload set mixing an explicit-object and a normal member function"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct MWidget {
            int value = 50;
            int get(this MWidget& self) { return self.value; }
            int get(int extra) { return value + extra; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.MWidget()
        assert w.get() == 50          # explicit-object overload
        assert w.get(7) == 57         # normal overload

    def test10_deducing_this_templated(self):
        """templated explicit object parameter (the CRTP-replacement idiom)"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct TWidget {
            int value = 9;
            template <class Self>
            int via(this Self&& self) { return self.value; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.TWidget()
        assert w.via() == 9

    def test11_deducing_this_templated_with_args(self):
        """templated explicit object parameter alongside a regular argument"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct TAWidget {
            int base = 40;
            template <class Self>
            int plus(this Self&& self, int x) { return self.base + x; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.TAWidget()
        assert w.plus(2) == 42

    def test12_deducing_this_templated_returns_self_type(self):
        """deduced Self drives the return: returns the deduced object's field"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct TRWidget {
            int value = 99;
            template <class Self>
            auto identity(this Self&& self) { return self.value; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.TRWidget()
        assert w.identity() == 99

    def test13_deducing_this_abbreviated_auto(self):
        """abbreviated `this auto&&` form (the canonical CRTP-replacement idiom)"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct AAWidget {
            int value = 23;
            int get(this auto&& self) { return self.value; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.AAWidget()
        assert w.get() == 23

    def test14_deducing_this_by_value_copy_semantics(self):
        """by-value `this W self` operates on an independent copy"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct CopyWidget {
            int value = 1;
            int bump(this CopyWidget self) { self.value += 100; return self.value; }
        };
        }
        """)

        w = cppyy.gbl.Cpp23DeducingThis.CopyWidget()
        assert w.bump() == 101        # the copy is mutated
        assert w.value == 1           # ... the original is untouched

    def test15_deducing_this_inheritance(self):
        """base-class explicit object method invoked on a derived object"""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct Base {
            int value = 8;
            int get(this Base& self) { return self.value; }
        };
        struct Derived : Base { };
        }
        """)

        d = cppyy.gbl.Cpp23DeducingThis.Derived()
        assert d.get() == 8

    # ------------------------------------------------------------------ #
    # Use-cases from the Microsoft C++ blog post "C++23's Deducing this":
    # https://devblogs.microsoft.com/cppblog/cpp23-deducing-this/
    # ------------------------------------------------------------------ #

    def test16_blog_deduplication(self):
        """Blog use-case 1: code de-duplication of cv/ref accessors."""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        #include <utility>
        namespace Cpp23DeducingThis {
        struct Optional {
            int m_value = 5;
            // one accessor, all value categories (returns a reference)
            template <class Self> auto&& value(this Self&& self) {
                return std::forward<Self>(self).m_value;
            }
            // by-value flavor, for a clean read from Python
            template <class Self> auto read(this Self&& self) {
                return std::forward<Self>(self).m_value;
            }
        };
        }
        """)

        o = cppyy.gbl.Cpp23DeducingThis.Optional()
        assert o.read() == 5                 # forwarding read
        o.value()[0] = 17                    # write through the forwarded reference
        assert o.read() == 17                # ... mutation is visible on the object

    def test17_blog_crtp_postfix_increment(self):
        """Blog use-case 2: CRTP postfix increment without templating the base.

        The using-declaration re-exposes the inherited postfix (standard name
        hiding); driven from C++ as Python has no postfix-increment syntax.
        """
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct add_postfix_increment {
            template <typename Self>
            auto operator++(this Self&& self, int) { auto tmp = self; ++self; return tmp; }
        };
        struct some_type : add_postfix_increment {
            using add_postfix_increment::operator++;   // un-hide inherited postfix
            int v = 0;
            some_type& operator++() { ++v; return *this; }
        };
        // old.v should be the pre-increment value, c.v the post.
        int drive_postfix() { some_type c; auto old = c++; return old.v * 100 + c.v; }
        }
        """)

        assert cppyy.gbl.Cpp23DeducingThis.drive_postfix() == 1   # old.v=0, c.v=1

    def test18_blog_recursive_lambda(self):
        """Blog use-case 4: recursive lambda via the explicit object parameter."""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        int fib(int n) {
            auto f = [](this auto const& self, int n) -> int {
                return n < 2 ? n : self(n - 1) + self(n - 2);
            };
            return f(n);
        }
        }
        """)

        assert cppyy.gbl.Cpp23DeducingThis.fib(10) == 55

    def test19_blog_lambda_forwarding(self):
        """Blog use-case 3: closure with an explicit object parameter.

        The blog uses std::forward_like (not in the host libstdc++); this
        exercises the explicit-object closure mechanism itself.
        """
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        #include <utility>
        namespace Cpp23DeducingThis {
        struct Scheduler { int submitted = 0; int submit(int m) { submitted = m; return m; } };
        int run_callback() {
            Scheduler scheduler;
            int message = 42;
            auto callback = [message, &scheduler](this auto&& self) -> int {
                return scheduler.submit(message);
            };
            return callback();
        }
        }
        """)

        assert cppyy.gbl.Cpp23DeducingThis.run_callback() == 42

    def test20_blog_pass_by_value(self):
        """Blog use-case 5: pass the object by value for better codegen on small types."""
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        struct just_a_little_guy {
            int how_smol = 21;
            int uwu(this just_a_little_guy self) { return self.how_smol * 2; }
        };
        }
        """)

        assert cppyy.gbl.Cpp23DeducingThis.just_a_little_guy().uwu() == 42

    def test21_blog_sfinae_friendly_transform(self):
        """Blog use-case 6: SFINAE-friendly optional::transform.

        Driven from C++: cppyy can't resolve a two-template-parameter
        explicit-object method against a Python callable.
        """
        cppyy = self.cppyy

        assert cppyy.cppdef("""
        namespace Cpp23DeducingThis {
        template <class T>
        struct Optional6 {
            T m_value;
            template <class Self, class F>
            auto transform(this Self&& self, F&& f) { return f(self.m_value); }
        };
        int triple(int x) { return x * 3; }
        int drive_transform() { Optional6<int> o{14}; return o.transform(triple); }
        }
        """)

        assert cppyy.gbl.Cpp23DeducingThis.drive_transform() == 42


@mark.skipif(_IN_CHILD, reason="launcher runs only in the parent process")
class TestCPP23Driver:
    """Re-run TestCPP23FEATURES once in a child interpreter pinned to C++23."""

    def test_run_under_cpp23(self):
        env = dict(os.environ)
        env[_CPP23_CHILD] = "1"
        env["EXTRA_CLING_ARGS"] = "-std=c++23"                   # cling
        env["CPPINTEROP_EXTRA_INTERPRETER_ARGS"] = "-std=c++23"  # clang-repl
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             os.path.basename(__file__)],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env, capture_output=True, text=True)
        assert proc.returncode == 0, (
            "C++23 child run failed (rc=%d)\n--- stdout ---\n%s\n--- stderr ---\n%s"
            % (proc.returncode, proc.stdout, proc.stderr))
