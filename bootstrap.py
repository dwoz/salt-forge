
REQUIREMENTS = [
    'PyYaml',
]


def activate(path):
    import os
    activate = os.path.join(path, 'bin', 'activate_this.py')
    execfile(activate, dict(__file__=activate))


def create_env(path, requirements=REQUIREMENTS):
    import imp, io, os, subprocess
    try:
        import virtualenv, textwrap
    except ImportError:
        import sys
        sys.stderr.write("virtualenv required.\n")
        sys.stderr.flush()
        sys.exit(1)
    output = virtualenv.create_bootstrap_script(textwrap.dedent("""
    import os, subprocess
    def after_install(options, home_dir):
        etc = join(home_dir, 'etc')
        if not os.path.exists(etc):
            os.makedirs(etc)
    """))
    module_name = 'envboot'
    module_path = '{}.py'.format(module_name)
    with open(module_path, 'w') as fp:
        fp.write(output)
    fp, pathname, desc = imp.find_module(module_name)
    envboot = imp.load_module(module_name, fp, pathname, desc)
    envboot.create_environment(path,
                       site_packages=False,
                       clear=False,
                       prompt=None,
                       search_dirs=envboot.file_search_dirs(),
                       download=True,
                       no_setuptools=False,
                       no_pip=False,
                       no_wheel=False,
                       symlink=True)
    if os.path.exists(module_path):
        os.remove(module_path)
    if os.path.exists(module_path + 'c'):
        os.remove(module_path + 'c')

    reqfile = 'requirements.txt'
    with open(reqfile, 'w') as fp:
        fp.write(os.linesep.join(requirements))
    pip_path = os.path.join(path, 'bin', 'pip')
    cmd = '{} install -r {}'.format(pip_path, reqfile)
    subprocess.check_call(cmd, shell=True)
    os.remove(reqfile)


if __name__ == '__main__':
    import os
    bootstrap_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv'))
