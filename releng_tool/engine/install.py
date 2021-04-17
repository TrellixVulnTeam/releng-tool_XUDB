# -*- coding: utf-8 -*-
# Copyright 2018-2021 releng-tool

from releng_tool.api import RelengInstallOptions
from releng_tool.defs import PackageInstallType
from releng_tool.defs import PackageType
from releng_tool.engine.autotools.install import install as install_autotools
from releng_tool.engine.cmake.install import install as install_cmake
from releng_tool.engine.python.install import install as install_python
from releng_tool.engine.script.install import install as install_script
from releng_tool.util import nullish_coalescing as NC
from releng_tool.util.api import package_install_type_to_api_type
from releng_tool.util.api import replicate_package_attribs
from releng_tool.util.io import interim_working_dir
from releng_tool.util.log import err
from releng_tool.util.log import note
import sys

def stage(engine, pkg, script_env):
    """
    handles the installation stage for a package

    With a provided engine and package instance, the installation stage will be
    processed.

    Args:
        engine: the engine
        pkg: the package being built
        script_env: script environment information

    Returns:
        ``True`` if the installation stage is completed; ``False`` otherwise
    """

    note('installing {}...'.format(pkg.name))
    sys.stdout.flush()

    if pkg.build_subdir:
        build_dir = pkg.build_subdir
    else:
        build_dir = pkg.build_dir

    if pkg.install_type == PackageInstallType.HOST:
        dest_dirs = [engine.opts.host_dir]
    elif pkg.install_type == PackageInstallType.IMAGES:
        dest_dirs = [engine.opts.images_dir]
    elif pkg.install_type == PackageInstallType.STAGING:
        dest_dirs = [engine.opts.staging_dir]
    elif pkg.install_type == PackageInstallType.STAGING_AND_TARGET:
        dest_dirs = [engine.opts.staging_dir, engine.opts.target_dir]
    else:
        # default to target directory
        dest_dirs = [engine.opts.target_dir]

    install_opts = RelengInstallOptions()
    replicate_package_attribs(install_opts, pkg)
    install_opts.build_dir = build_dir
    install_opts.build_output_dir = pkg.build_output_dir
    install_opts.cache_file = pkg.cache_file
    install_opts.def_dir = pkg.def_dir
    install_opts.dest_dirs = dest_dirs
    install_opts.env = script_env
    install_opts.ext = pkg.ext_modifiers
    install_opts.host_dir = engine.opts.host_dir
    install_opts.images_dir = engine.opts.images_dir
    install_opts.install_defs = pkg.install_defs
    install_opts.install_env = pkg.install_env
    install_opts.install_opts = pkg.install_opts
    install_opts.install_type = package_install_type_to_api_type(pkg.install_type)
    install_opts.name = pkg.name
    install_opts.prefix = NC(pkg.prefix, engine.opts.sysroot_prefix)
    install_opts.staging_dir = engine.opts.staging_dir
    install_opts.symbols_dir = engine.opts.symbols_dir
    install_opts.target_dir = engine.opts.target_dir
    install_opts.version = pkg.version
    install_opts._quirks = engine.opts.quirks

    installer = None
    if pkg.type in engine.registry.package_types:
        def _(opts):
            return engine.registry.package_types[pkg.type].install(
                pkg.type, opts)
        installer = _
    elif pkg.type == PackageType.AUTOTOOLS:
        installer = install_autotools
    elif pkg.type == PackageType.CMAKE:
        installer = install_cmake
    elif pkg.type == PackageType.PYTHON:
        installer = install_python
    elif pkg.type == PackageType.SCRIPT:
        installer = install_script

    if not installer:
        err('installer type is not implemented: {}'.format(pkg.type))
        return False

    with interim_working_dir(build_dir):
        installed = installer(install_opts)
        if not installed:
            return False

    return True
