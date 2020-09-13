# -*- coding: utf-8 -*-
# Copyright 2019-2020 releng-tool

from ..util.io import interimWorkingDirectory
from ..util.io import optFile
from ..util.io import run_script
from ..util.log import *
import os
import sys

#: filename of the script to execute the post-processing operation (if any)
POST_SCRIPT = 'post'

def stage(engine, pkg, script_env):
    """
    handles the post-processing stage for a package

    With a provided engine and package instance, the post-processing stage will
    be processed. This stage is typically not advertised and is for advanced
    cases where a developer wishes to manipulate their build environment after
    package has completed each of its phases.

    Args:
        engine: the engine
        pkg: the package being built
        script_env: script environment information

    Returns:
        ``True`` if the post-processing stage is completed; ``False`` otherwise
    """

    verbose('post-processing {}...'.format(pkg.name))
    sys.stdout.flush()

    post_script_filename = '{}-{}'.format(pkg.name, POST_SCRIPT)
    post_script = os.path.join(pkg.def_dir, post_script_filename)
    post_script, post_script_exists = optFile(post_script)
    if not post_script_exists:
        return True

    if pkg.build_subdir:
        build_dir = pkg.build_subdir
    else:
        build_dir = pkg.build_dir

    with interimWorkingDirectory(build_dir):
        if not run_script(post_script, script_env, subject='post-processing'):
            return False

    verbose('post-processing script executed: ' + post_script)
    return True
