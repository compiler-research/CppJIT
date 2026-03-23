"""alias cppyy to cppjit.cppyy so upstream tests work unmodified."""
import sys

import cppjit
import cppjit.cppyy
import cppjit.cppyy_backend

sys.modules['cppyy'] = cppjit.cppyy
sys.modules['cppyy_backend'] = cppjit.cppyy_backend

disabled = None
