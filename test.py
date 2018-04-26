import os
import io
import yaml
import subprocess


def repo_name(url):
    _, name_with_git = rsplit('/', 1)
    return name_with_git.rsplit('.', 1)[0]


def main(config='config.yml'):
    orig_path = os.getcwd()
    with io.open(config, 'r') as fp:
        conf = yaml.safe_load(fp)

    # create root environments directory
    envs_dir = os.path.abspath(conf['envs_dir'])
    if not os.path.exists(envs_dir):
        os.makedirs(envs_dir)

    # create environments
    for env in conf['environments']:
        env_dir = os.path.join(envs_dir, env['name'])
        if not os.path.exists(env_dir):
            os.makedirs(env_dir)

        os.chdir(env_dir)

        ret = subprocess.call('git clone {}'.format(env['origin']), shell=True)
        if ret != 0:
            raise Exception("Bad return code from git clone")
        os.chdir(os.path.join(env_dir, 'salt'))

        for name, url in env['remotes'].items():
            ret = subprocess.call(
                'git remote add {} {}'.format(
                    name, url
                ),
                shell=True
            )
            if ret != 0:
                raise Exception("Bad return code from git remote add")


if __name__ == '__main__':
    main()
