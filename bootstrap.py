'''
bootenv.py

bootenv is capable of bootstraping a virtual environment even if the python
being used does not have setuptools or virtualenv installed. If there is no
setuptools installed in the pythong being used, a recent version of setuptools
is will be downloaded and used to install virtualenv. This script will not
install setuptools or virutalenv int the python environment. Instead, any
dependencies needed for bootstraping are downloaded to directory outside of the
normal python path and they are imported from this location when needed by
bootenv.
'''
import os
import distutils
import subprocess
import shutil
import sys
import logging
import time


logger = logging.getLogger(__name__)

REQUIREMENTS = [
    'PyYaml',
]

walk = os.path.walk
if hasattr(os, 'walk'):
    walk = os.walk

def fetch_url(url, out, verify=True):
    import urllib2
    import ssl
    if verify:
        context = ssl.create_default_context()
    else:
        context = ssl._create_unverified_context()
    response = urllib2.urlopen(url, context=context)
    with open(out, 'w') as fp:
       fp.write(response.read())

def unzip(zip_path, todir):
    import zipfile
    if not os.path.exists(todir):
        os.makedirs(todir)
    zip_ref = zipfile.ZipFile(zip_path, 'r')
    zip_ref.extractall(todir)
    zip_ref.close()
    for dirname, dirs, files in walk(todir):
        for name in dirs:
            return os.path.join(dirname, name)

def update_path(install_dir):
    pthfile = os.path.join(install_dir, 'easy-install.pth')
    if not os.path.exists(pthfile):
        return
    with open(pthfile) as fp:
        for line in fp:
            line = line.strip()
            if line.startswith('./'):
                sys.path.append(os.path.join(install_dir, line[2:]))
            else:
                sys.path.append(os.path.abspath(line))


def install_vendor(required, force=False):
    try:
        from setuptools.command import easy_install
        from setuptools.dist import Distribution
        from pkg_resources import Environment
    except ImportError:
        sys.stderr.write("setuptools is required.")
        sys.stderr.flush()
        sys.exit(1)

    base = os.path.abspath('./')
    install_dir = os.path.join(base, 'vendor')
    if not os.path.exists(install_dir):
        logger.debug("Creating vendor directory %s", install_dir)
        os.makedirs(install_dir)

    update_path(install_dir)
    if force:
        needed = required
    else:
        needed = []
        for name in required:
            try:
                __import__(name)
            except ImportError:
                needed.append(name)
        needed = required
        if not needed:
            logger.debug("Vendor modules loaded from %s", install_dir)
            return

    logger.debug(
        "Install requirements to vendors directory: %s %s",
        needed, install_dir
    )
    e = easy_install.easy_install(Distribution())
    e.install_dir = install_dir
    os.environ['PYTHONPATH'] = e.install_dir
    e.initialize_options()
    e.install_dir = install_dir
    e.args = required
    e.finalize_options()
    e.run()
    update_path(install_dir)
    for name in required:
        __import__(name)


def prereq():
    needed = []
    try:
        import virtualenv
    except:
        needed.append('virtualenv')
    try:
        import pip
    except:
        needed.append('pip')
    if needed:
        logger.debug("Site packages not found: %s", ', '.join(needed))
        install_vendor(needed)


def activate(path):
    import os
    activate = os.path.join(path, 'bin', 'activate_this.py')
    execfile(activate, dict(__file__=activate))


def create_env(path, requirements=REQUIREMENTS):
    prereq()
    import imp
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


def purge_module(name):
    pkg = name + '.'
    for modname in sys.modules:
        if modname.startswith(pkg):
            sys.modules.pop(modname)
        if modname == name:
            sys.modules.pop(modname)


def check_output(cmd, env=None, sleep=0.2, timeout=10, expected_return=0):
    proc = subprocess.Popen(cmd, shell=True, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ret = proc.poll()
    start = time.time()
    while ret is None:
        time.sleep(sleep)
        ret = proc.poll()
        if time.time() - start >= timeout:
            raise TimeoutError("Command timed out")
    out, err = proc.stdout.read(), proc.stderr.read()
    if ret != expected_return:
        logger.error("Command error output is %s", err)
        raise Exception("Command exited non 0: {} {}".format(ret, cmd))
    return out, err


def download_to_tmp(
        url = "https://github.com/pypa/setuptools/archive/v39.0.1.zip",
        #out = "v39.0.1.zip",
        tmp_prefix='tmp-salt-forge',
        ):
    '''
    Download setuptools and extract to a temporary directory
    '''
    import tempfile
    tmpdir = tempfile.mkdtemp(prefix=tmp_prefix)
    tmp_archive = os.path.join(tmpdir, 'setuptools.zip')
    fetch_url(url, tmp_archive)
    return os.path.abspath(unzip(tmp_archive, tmpdir)).strip()


def perform_bootstrap():
    logging.basicConfig(level = logging.DEBUG, message="%(asctime)s %(message)s)")
    logger.info("Fetch temporary setuptools")
    cmd = 'python {} stage1'.format(os.path.abspath(__file__))
    orig_path = os.getcwd()
    out, err = check_output(cmd)
    path = out.strip()
    os.chdir(path)
    logger.info("Run temporary setuptools bootstrap")
    setuptools_bootstrap = os.path.join(path, 'bootstrap.py')
    check_output('python {}/bootstrap.py'.format(path.strip()))
    os.chdir(orig_path)
    logger.info("Create vendor environment")
    check_output('python {} stage2'.format(__file__), env = {"PYTHONPATH": path})
    logger.debug("Remove temp directory: %s", path)
    shutil.rmtree(os.path.dirname(path))



if __name__ == '__main__':
    logging.basicConfig(level = logging.DEBUG, format="%(asctime)s %(message)s")
    if len(sys.argv) > 1 and sys.argv[1] == 'stage1':
        sys.dont_write_bytecode  = True
        print(download_to_tmp())
    elif len(sys.argv) > 1 and sys.argv[1] == 'stage2':
        sys.dont_write_bytecode  = True
        install_vendor(['setuptools'], force=True)
        prereq()
    else:
        perform_bootstrap()
        update_path('vendor')
        _envdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.venv')
        create_env(_envdir)
