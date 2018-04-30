_activate = lambda x : execfile(x, dict(__file__=x))
_activate_paths = (
    'venv/bin/activate_this.py',
)
for _path in _activate_paths:
    try:
        _activate(_path)
    except:
        continue
    print("Using virtualenv: {}".format(_path))
    break
import os
import io
import yaml
import subprocess
import argparse


parser = argparse.ArgumentParser(description='Slat Forge')
parser.add_argument('name')


def repo_name(url):
    _, name_with_git = rsplit('/', 1)
    return name_with_git.rsplit('.', 1)[0]


def run(cmd):
    ret = subprocess.call(cmd, shell=True)
    if ret != 0:
        raise Exception("Bad return code from git config")

def main(config='config.yml'):
    ns = parser.parse_args()
    orig_path = os.getcwd()
    with io.open(config, 'r') as fp:
        conf = yaml.safe_load(fp)

    # create root environments directory
    if os.sep in ns.name:
        path = os.path.abspath(ns.name)
        name = os.path.basename(path)
        envs_dir = os.path.dirname(path)
    else:
        name = ns.name
        envs_dir = os.path.abspath(os.getcwd())
    if not os.path.exists(envs_dir):
        os.makedirs(envs_dir)

    env_dir = os.path.join(envs_dir, name)
    if not os.path.exists(env_dir):
        os.makedirs(env_dir)

    os.chdir(env_dir)

    cmd = 'git clone '
    if 'branch' in conf['git'] and conf['git']['branch'] > 0:
        cmd += '--branch {} '.format(conf['git']['branch'])
    if 'depth' in conf['git'] and conf['git']['depth'] > 0:
        cmd += '--depth {} '.format(conf['git']['depth'])
    cmd += conf['git']['origin']
    subprocess.check_call(cmd, shell=True)

    os.chdir(os.path.join(env_dir, 'salt'))

    for key, val in conf['git']['config'].items():
        cmd = 'git config --local {} \'{}\''.format(key, val)
        subprocess.check_call(cmd, shell=True)

    for name, url in conf['git']['remotes'].items():
        ret = subprocess.call(
            'git remote add {} {}'.format(
                name, url
            ),
            shell=True
        )
        if ret != 0:
            raise Exception("Bad return code from git remote add")

    os.chdir(env_dir)

    cmd = 'virtualenv venv --python={}'.format(conf['python'])
    subprocess.check_call(cmd, shell=True)

    cmd = 'venv/bin/pip install -e salt'
    subprocess.check_call(cmd, shell=True)

    for path in conf['files']:
        full_path = os.path.join(env_dir, path)
        dir_path = os.path.dirname(full_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(full_path, 'w') as fp:
            yaml.dump(conf['files'][path], fp, default_flow_style=False)


if __name__ == '__main__':
    main()
