# -*- coding: utf-8 -*-
# Copyright 2018-2022 releng-tool

from importlib import import_module
from releng_tool import __version__ as releng_version
from releng_tool.api import RelengInvalidSetupException
from releng_tool.api import RelengRegistryInterface
from releng_tool.api import RelengVersionNotSupportedException
from releng_tool.support import require_version
from releng_tool.util.log import debug
from releng_tool.util.log import verbose
from releng_tool.util.log import warn
from releng_tool.util.string import interpret_string
import sys

if sys.version_info < (3, 0):
    import imp

try:
    RelengModuleNotFoundError = ModuleNotFoundError
except NameError:
    RelengModuleNotFoundError = ImportError


#: prefix requirement for extension named types
PREFIX_REQUIREMENT = 'ext-'


class RelengRegistry(RelengRegistryInterface):
    """
    extension registry

    Registry provides a means for external implementation to hook into various
    stages of a release engineering process.

    Attributes:
        extension: list of registered extensions
        extract_types: registered extraction handlers
        fetch_types: registered fetch handlers
        package_types: registered package handlers
    """
    def __init__(self):
        self.extension = []
        self.extract_types = {}
        self.fetch_types = {}
        self.package_types = {}

        # always load base/example extension
        self.load('releng_tool.ext.seed')

    def load_all_extensions(self, names):
        """
        load all provided extensions into the registry

        Attempts to load all extensions provides in the names collection. If an
        extension which is already loaded in the registry is provided, the
        request to load the specific extension is ignored. If an extension could
        not be loaded, a warning is generated and this method will return
        ``False``. This method will continue to load extensions, even if a
        single extension in the collection fails to load.

        Args:
            names: names of the extensions to load

        Returns:
            whether or not all extensions are loaded in the registry
        """
        loaded = True
        for name in names:
            if not self.load(name):
                loaded = False
        return loaded

    def load(self, name, ignore=True):
        """
        load the provided extension into the registry

        Attempts to load an extension with the provided name value. If an
        extension which is already loaded in the registry is provided, the
        request to load the specific extension is ignored. If an extension could
        not be loaded, a warning is generated and this method will return
        ``False``.

        Args:
            name: name of the extension to load
            ignore (optional): ignore if the detected extension could not be
                                loaded (default: True)

        Returns:
            whether or not the extension was loaded in the registry
        """

        # ignore if extension is already loaded
        if name in self.extension:
            return True

        loaded = False
        debug('attempting to load extension: {}', name)
        try:
            try:
                plugin = import_module(name)
            except RelengModuleNotFoundError:
                # python 2.7 may not be able to load from a nested path; try
                # searching through each package (if a nested module)
                if sys.version_info >= (3, 0) or '.' not in name:
                    raise

                # split the module into parts and for each part, check to see
                # if it's a package directory; if so, keep going until the last
                # namespace package
                ext_parts = name.split('.')
                path = None
                for part in ext_parts[:-1]:
                    file, pathname, desc = imp.find_module(part, path)

                    if desc[-1] != imp.PKG_DIRECTORY:
                        raise ImportError(name)

                    pkg = imp.load_module(part, file, pathname, desc)
                    path = pkg.__path__

                # with the path of the last namespace package found, find the
                # desired module in this path
                last_part = ext_parts[-1]
                file, pathname, desc = imp.find_module(last_part, path)
                plugin = imp.load_module(last_part, file, pathname, desc)

            if hasattr(plugin, 'releng_setup'):
                if not ignore:
                    plugin.releng_setup(self)
                    loaded = True
                else:
                    try:
                        plugin.releng_setup(self)
                        loaded = True
                    except RelengInvalidSetupException as e:
                        warn('extension is not supported '
                             'due to an invalid setup: {}\n'
                             ' ({})', name, e)
                    except RelengVersionNotSupportedException as e:
                        warn('extension is not supported '
                             'with this version: {}\n'
                             ' ({})', name, e)

                if loaded:
                    self.extension.append(name)
                    verbose('loaded extension: {}', name)
                    loaded = True
            else:
                warn('extension does not have a setup method: {}', name)
        except RelengModuleNotFoundError:
            warn('unable to find extension: {}', name)

        return loaded

    def add_extract_type(self, name, handler):
        """
        register extraction support with a given name for this extension

        An extension will invoke this method will attempting to support a custom
        extraction method for a release engineering process. The extraction
        type is identified by the provided ``name`` value. Packages being
        processed with VCS type paired with a extension-defined fetch type or a
        package extraction override will be processed through the provided
        `handler``.

        An extension must define a proper ``name`` for the extract-type:

         - The name is a string value.
         - The name must be prefixed with ``ext-``.
         - The name should be all lowercase.
         - The dash character ``-`` is the recommended separator.

        The ``handler`` must be compatible with the implementation defined in
        ``RelengExtractExtensionInterface``. There is no requirement that the
        handler needs to inherit this interface.

        Additional notes:

         - The releng-tool process may instantiation one or more of the provided
            handler types.
         - The first extension loaded with a custom extract-type will take
            precedence over other extensions.

        Args:
            name: the name of this extract type
            handler: the extract-type class handler

        Raises:
            RelengInvalidSetupException: raised when the provided ``name`` or
                ``handler`` values are not supported by the releng-tool process
        """
        if not interpret_string(name):
            raise RelengInvalidSetupException('invalid extract name provided')
        name_key = name.lower()
        if not name_key.startswith(PREFIX_REQUIREMENT):
            raise RelengInvalidSetupException('extension-defined extract types '
                'must be prefixed with "{}"'.format(PREFIX_REQUIREMENT))
        if name_key in self.extract_types:
            raise RelengInvalidSetupException('extension extract type {} is '
                'already defined by another extension'.format(name))
        extract_type = handler()
        extract_op = getattr(extract_type, 'extract', None)
        if not callable(extract_op):
            raise RelengInvalidSetupException('extract type does not defined '
                'required method(s)')
        self.extract_types[name_key] = extract_type

    def add_fetch_type(self, name, handler):
        """
        register fetch support with a given name for this extension

        An extension will invoke this method will attempting to support a custom
        fetch method for a release engineering process. The fetch type is
        identified by the provided ``name`` value. Packages being processed with
        a matching VCS type will be processed through the provided ``handler``.

        An extension must define a proper ``name`` for the fetch-type:

         - The name is a string value.
         - The name must be prefixed with ``ext-``.
         - The name should be all lowercase.
         - The dash character ``-`` is the recommended separator.

        The ``handler`` must be compatible with the implementation defined in
        ``RelengFetchExtensionInterface``. There is no requirement that the
        handler needs to inherit this interface.

        Additional notes:

         - The releng-tool process may instantiation one or more of the provided
            handler types.
         - The first extension loaded with a custom fetch-type will take
            precedence over other extensions.

        Args:
            name: the name of this fetch type
            handler: the fetch-type class handler

        Raises:
            RelengInvalidSetupException: raised when the provided ``name`` or
                ``handler`` values are not supported by the releng-tool process
        """
        if not interpret_string(name):
            raise RelengInvalidSetupException('invalid fetch name provided')
        name_key = name.lower()
        if not name_key.startswith(PREFIX_REQUIREMENT):
            raise RelengInvalidSetupException('extension-defined fetch types '
                'must be prefixed with "{}"'.format(PREFIX_REQUIREMENT))
        if name_key in self.fetch_types:
            raise RelengInvalidSetupException('extension fetch type {} is '
                'already defined by another extension'.format(name))
        fetch_type = handler()
        fetch_op = getattr(fetch_type, 'fetch', None)
        if not callable(fetch_op):
            raise RelengInvalidSetupException('fetch type does not defined '
                'required method(s)')
        self.fetch_types[name_key] = fetch_type

    def add_package_type(self, name, handler):
        """
        register package support with a given name for this extension

        An extension will invoke this method will attempting to support a custom
        package methods for a release engineering process. The package type is
        identified by the provided ``name`` value. Packages being processed with
        a matching type will be processed through the provided ``handler`` for
        each package stage (configuration, building, etc.).

        An extension must define a proper ``name`` for the package-type:

         - The name is a string value.
         - The name must be prefixed with ``ext-``.
         - The name should be all lowercase.
         - The dash character ``-`` is the recommended separator.

        The ``handler`` must be compatible with the implementation defined in
        ``RelengPackageExtensionInterface``. There is no requirement that the
        handler needs to inherit this interface.

        Additional notes:

         - The releng-tool process may instantiation one or more of the provided
            handler types.
         - The first extension loaded with a custom package-type will take
            precedence over other extensions.

        Args:
            name: the name of this package type
            handler: the package-type class handler

        Raises:
            RelengInvalidSetupException: raised when the provided ``name`` or
                ``handler`` values are not supported by the releng-tool process
        """
        if not interpret_string(name):
            raise RelengInvalidSetupException('invalid package name provided')
        name_key = name.lower()
        if not name_key.startswith(PREFIX_REQUIREMENT):
            raise RelengInvalidSetupException('extension-defined package types '
                'must be prefixed with "{}"'.format(PREFIX_REQUIREMENT))
        if name_key in self.package_types:
            raise RelengInvalidSetupException('extension package type {} '
                'is already defined by another extension'.format(name))
        package_type = handler()
        build_op = getattr(package_type, 'build', None)
        configure_op = getattr(package_type, 'configure', None)
        install_op = getattr(package_type, 'install', None)
        if (not callable(build_op) or not callable(configure_op) or
                not callable(install_op)):
            raise RelengInvalidSetupException('package type does not defined '
                'required method(s)')
        self.package_types[name_key] = package_type

    def require_version(self, version):
        """
        perform a required-version check

        Enables an extension to explicitly check for a required releng-tool
        version before being loaded. Invoking this method with a
        dotted-separated ``version`` string, the string will be parsed and
        compared with the running releng-tool version. If the required version
        is met, this method will have no effect. In the event that the required
        version is not met, the exception ``RelengVersionNotSupportedException``
        will be raised. The extension implementation does not need to explicitly
        handle this exception (as it is caught by the registry loading process).

        Args:
            version: dotted-separated version string

        Raises:
            RelengVersionNotSupportedException: raised when the required version
                for this extension is not met
        """

        if not require_version(version, quiet=True, critical=False):
            raise RelengVersionNotSupportedException(
                'requires {}, has {}'.format(version, releng_version))
