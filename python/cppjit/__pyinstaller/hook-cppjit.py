# PyInstaller hooks to declare the "data files" (libraries, headers, etc.) of
# cppjit-backend. Placed here rather then in cppjit-backend to guarantee that any
# packaging of top-level "cppjit" picks up the backend as well.
#
# See also setup.cfg.

__all__ = ['data']


def _backend_files():
    import cppjit_backend, glob, os

    all_files = glob.glob(os.path.join(
        os.path.dirname(cppjit_backend.__file__), '*'))

    def datafile(path):
        return path, os.path.join('cppjit_backend', os.path.basename(path))

    return [datafile(filename) for filename in all_files if os.path.isdir(filename)]

def _api_files():
    import cppjit, os

    # FIXME: We should add an interface in InterOp.
    paths = str(cppjit.gbl.runtime.gCling.GetIncludePath()).split('-I')
    for p in paths:
        if not p: continue

        apipath = os.path.join(p.strip()[1:-1], 'cpyrt')
        if os.path.exists(apipath):
            return [(apipath, os.path.join('include', 'cpyrt'))]

    return []

datas = _backend_files()+_api_files()
