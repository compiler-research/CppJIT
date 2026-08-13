#ifndef CPYRT_MEMORYREGULATOR_H
#define CPYRT_MEMORYREGULATOR_H

#include "Python.h"
#include "cppjit_interop.h"

#include <functional>
#include <utility>

namespace cppjit::cpyrt {

class CPPInstance;

typedef std::function<std::pair<bool, bool>(cppjit::interop::TCppObject_t,
                                            cppjit::interop::TCppScope_t)>
    MemHook_t;

class MemoryRegulator {
private:
  static MemHook_t registerHook, unregisterHook;

public:
  MemoryRegulator();

  // callback from C++-side frameworks
  static bool RecursiveRemove(cppjit::interop::TCppObject_t cppobj,
                              cppjit::interop::TCppScope_t klass);

  // called when a new python proxy object is created
  static bool RegisterPyObject(CPPInstance* pyobj,
                               cppjit::interop::TCppObject_t cppobj);

  // called when a the python proxy object is about to be garbage collected or
  // when it is about to delete the proxied C++ object, if owned
  static bool UnregisterPyObject(CPPInstance* pyobj, PyObject* pyclass);

  // new reference to python object matching cppobj, or 0 on failure
  static PyObject* RetrievePyObject(cppjit::interop::TCppObject_t cppobj,
                                    PyObject* pyclass);

  // set hooks for custom memory regulation
  static void SetRegisterHook(MemHook_t h);
  static void SetUnregisterHook(MemHook_t h);
};

} // namespace cppjit::cpyrt

#endif // !CPYRT_MEMORYREGULATOR_H
