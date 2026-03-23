from __future__ import print_function
import os, sys, subprocess

MYHOME = os.path.dirname(__file__)

def main():
    if len(sys.argv) == 2:
        options = sys.argv[1]

        if options == '--cmake':
            print(os.path.join(MYHOME, "cmake"))
            return 0

        if options == '--cppflags':
            options = '--cflags'

        if options != '--help':
            rcfg = os.path.join(MYHOME, 'bin', 'root-config')
            try:
                cli_arg = subprocess.check_output(
                    [os.path.join(MYHOME, 'bin', 'root-config'), options],
                    stderr=subprocess.STDOUT)
                out = cli_arg.decode("utf-8").strip()
                if 'flags' in options and 'STDCXX' in os.environ and '-std=' in out:
                    req = os.environ['STDCXX']
                    true_flags = None
                    if req == '17':
                        true_flags = '-std=c++1z'
                    elif req == '20':
                        true_flags = '-std=c++2a'
                    else:
                        true_flags = '-std=c++'+req
                    if true_flags:
                        pos = out.find('std=')
                        out = out[:pos] + true_flags + out[pos+9:]
                print(out)
                return 0
            except OSError:
                if not os.path.exists(rcfg) or not 'win32' in sys.platform:
                    raise

                # happens on Windows b/c root-config is a bash script; the
                # following covers the most important options until that
                # gets fixed upstream

                def get_include_dir():
                    return os.path.join(MYHOME, 'include')

                def get_library_dir():
                    return os.path.join(MYHOME, 'lib')

                def get_basic_cppflags():
                    flags = '-Zc:__cplusplus '
                    if 'STDCXX' in os.environ:
                        return flags + '/std:c++'+os.environ['STDCXX']
                    else:
                        for line in open(rcfg):
                            if 'cxxversion' in line:
                                if '11' in line:
                                    return flags+'/std:c++11'
                                elif '14' in line:
                                    return flags+'/std:c++14'
                                elif '17' in line:
                                    return flags+'/std:c++17'
                                else:
                                  # includes C++20, which won't get it's own flag until
                                  # it is feature-complete
                                    return flags+'/std:c++latest'
                        raise

                if options == '--incdir':
                    print(get_include_dir())
                    return 0

                elif options == '--libdir':
                    print(get_library_dir())
                    return 0

                elif options == '--auxcflags':
                # most important is get the C++ version flag right
                    print(get_basic_cppflags())
                    return 0

                elif options == '--cflags':
                # most important are C++ flag and include directory
                    print(get_basic_cppflags(), '/I'+get_include_dir(), '/FIw32pragma.h')
                    return 0

                elif options == '--ldflags':
                    print('/LIBPATH:'+get_library_dir(), 'libCoreLegacy.lib', 'libRIOLegacy.lib')
                    return 0

            except subprocess.CalledProcessError:
                pass

    print('Usage: cling-config [--cflags] [--cppflags] [--cmake]')
    return 1

if __name__ == '__main__':
    sys.exit(main())
