# -*- coding: utf-8 -*-
# Copyright 2018-2022 releng-tool

from releng_tool.tool.python import PYTHON
from releng_tool.tool.python import PYTHON_EXTEND_ENV
from releng_tool.tool.python import PythonTool
from releng_tool.util.io import generate_temp_dir
from releng_tool.util.io import path_move
from releng_tool.util.io import prepare_arguments
from releng_tool.util.io import prepare_definitions
from releng_tool.util.log import err
from releng_tool.util.string import expand
import os


def install(opts):
    """
    support installation python projects

    With provided installation options (``RelengInstallOptions``), the
    installation stage will be processed.

    Args:
        opts: installation options

    Returns:
        ``True`` if the installation stage is completed; ``False`` otherwise
    """

    if opts._python_interpreter:
        python_tool = PythonTool(opts._python_interpreter,
            env_include=PYTHON_EXTEND_ENV)
    else:
        python_tool = PYTHON

    if not python_tool.exists():
        err('unable to install package; python is not installed')
        return False

    # definitions
    python_defs = {
    }

    # do not apply a prefix if the value is "empty"/(root path) since a
    # setup.py invoke may ignore provided `--root` value or `--prefix` value;
    # apply if it is set; otherwise flag for manipulation
    if opts.prefix and opts.prefix != os.sep:
        python_defs['--prefix'] = opts.prefix

    if opts.install_defs:
        python_defs.update(expand(opts.install_defs))

    # default environment
    path0 = python_tool.path(sysroot=opts.host_dir, prefix=opts.prefix)
    path1 = python_tool.path(sysroot=opts.staging_dir, prefix=opts.prefix)
    path2 = python_tool.path(sysroot=opts.target_dir, prefix=opts.prefix)
    env = {
        'PYTHONPATH': path0 + os.pathsep + path1 + os.pathsep + path2
    }

    # apply package-specific environment options
    if opts.install_env:
        env.update(expand(opts.install_env))

    # default options
    python_opts = {
    }

    # avoid building pyc files for non-host packages
    if opts.install_type != 'host':
        python_opts['--no-compile'] = ''

    if opts.install_opts:
        python_opts.update(expand(opts.install_opts))

    # argument building
    python_args = [
        'setup.py',
        # ignore user's pydistutils.cfg
        '--no-user-cfg',
        # invoke the install operation
        'install',
    ]

    python_args.extend(prepare_definitions(python_defs))
    python_args.extend(prepare_arguments(python_opts))

    # install to target destination(s)
    #
    # If the package already defines a root path, use it over any other
    # configured destination directories.
    if '--root' in python_opts:
        if not python_tool.execute(python_args, env=env):
            err('failed to install python project: {}', opts.name)
            return False
    else:
        # install to each destination
        for dest_dir in opts.dest_dirs:
            if '--prefix' not in python_defs:
                # for empty prefixes, we will need to install the package into
                # an interim container folder (temporary prefix) of distutils
                # will apply a default prefix for a desired empty prefix -- we
                # set a temporary prefix, install the package in that folder,
                # then move it into the desired destination folder
                with generate_temp_dir() as tmp_dir:
                    container = 'releng-tool-container'

                    python_args_tmp = python_args
                    python_args_tmp.extend(['--prefix', container])

                    rv = python_tool.execute(
                        python_args_tmp + ['--root', tmp_dir], env=env)

                    if rv:
                        src_dir = os.path.join(tmp_dir, container) + os.sep
                        path_move(src_dir, dest_dir)
            else:
                rv = python_tool.execute(
                    python_args + ['--root', dest_dir], env=env)

            if not rv:
                err('failed to install python project: {}', opts.name)
                return False

    return True
