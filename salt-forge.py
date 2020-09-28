#!/usr/bin/env python
import os
import salt_forge_bootstrap

user_config_path = os.path.join(os.path.expanduser('~'), '.local', 'salt-forge')
if not os.path.exists(user_config_path):
    os.makedirs(user_config_path)
_envdir = os.path.join(user_config_path, '.venv')

requirements = [
    'PyYaml',
#    '-e git://github.com:saltstack/salt.git@v2018.3.1#egg=salt',
]

if not os.path.exists(_envdir):
    salt_forge_bootstrap.create_env(
        _envdir,
        requirements=requirements,
    )
salt_forge_bootstrap.activate(_envdir)

import logging
import sys
import os
import io
import yaml
import subprocess
import argparse


logger = logging.getLogger(__name__)
parser = argparse.ArgumentParser(description='Salt Forge - Forge Salt environments at will')
parser.add_argument('name')

#def get_base_prefix_compat():
#    return getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix
#
#def in_virtualenv():
#    return get_base_prefix_compat() != sys.prefix

def repo_name(url):
    _, name_with_git = rsplit('/', 1)
    return name_with_git.rsplit('.', 1)[0]


def find_config(config='config.yml'):
    for path in ['.', os.path.join(os.path.expanduser('~'), '.local', 'salt-forge')]:
        check_path = os.path.join(path, config)
        if os.path.exists(check_path):
            return check_path
    raise Exception("Unable to find config")


def main(config='config.yml'):

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(message)s")

    # XXX: Add vendor to path?
    venv_bin = 'virtualenv'
    if os.path.exists('vendor/virtualenv.exe'):
        venv_bin = os.path.abspath('vendor/virtualenv.exe')
    elif os.path.exists('vendor/virtualenv'):
        venv_bin = os.path.abspath('vendor/virtualenv')

    ns = parser.parse_args()
    orig_path = os.getcwd()
    config_path = find_config(config)
    print("READ CONFIG PATH {}".format(config_path))
    with io.open(config_path, 'r') as fp:
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

    # clone and configure git repositories
    for key, git_conf in conf['git'].items():
        os.chdir(env_dir)
        git_dir = os.path.join(env_dir, key)
        if not os.path.exists(os.path.dirname(git_dir)):
            os.makedirs(os.path.dirname(git_dir))

        cmd = 'git clone '
        if 'branch' in git_conf:
            cmd += '--branch {} '.format(git_conf['branch'])
        if 'depth' in git_conf and git_conf['depth'] > 0:
            cmd += '--depth {} '.format(git_conf['depth'])
        cmd = '{} {} {}'.format(cmd, git_conf['origin'], key)

        logger.info('Running command %s', cmd)
        subprocess.check_call(cmd, shell=True)

        os.chdir(os.path.join(env_dir, key))

        for key, val in git_conf['config'].items():
            cmd = [
                'git',
                'config',
                '--local',
                '{}'.format(key),
                '{}'.format(val),
            ]
            subprocess.check_call(cmd)

        for name, url in git_conf.get('remotes', {}).items():
            ret = subprocess.call(
                'git remote add {} {}'.format(
                    name, url
                ),
                shell=True
            )
            if ret != 0:
                raise Exception("Bad return code from git remote add")

    os.chdir(env_dir)


    # Create a virtual environment
    cmd = '{} venv --python={}'.format(venv_bin, sys.executable)
    subprocess.check_call(cmd, shell=True)


    # Create a virtual environment
    for path in conf['files']:
        full_path = os.path.join(env_dir, path)
        dir_path = os.path.dirname(full_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(full_path, 'w') as fp:
            yaml.dump(conf['files'][path], fp, default_flow_style=False)

    envdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv')
    salt_forge_bootstrap.activate(_envdir)

    # Run commands
    for cmd in conf['commands']:
        logger.info("run command: %s".format(cmd))
        subprocess.check_call(cmd, shell=True)


if __name__ == '__main__':
    main()
