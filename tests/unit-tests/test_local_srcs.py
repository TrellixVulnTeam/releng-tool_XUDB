# -*- coding: utf-8 -*-
# Copyright 2021-2022 releng-tool

from releng_tool.util.io import ensure_dir_exists
from tests import RelengToolTestCase
from tests import copy_template
from tests import prepare_testenv
from tests import prepare_workdir as workdir
import json
import os
import uuid


class TestLocalSources(RelengToolTestCase):
    def test_localsrcs_default(self):
        with workdir() as test_dir:
            root_dir = os.path.join(test_dir, 'root')

            config = {
                'root_dir': root_dir,
            }

            copy_template('local-src', root_dir)
            pkga_val = self._dummy_pkg(test_dir, 'pkg-a')
            pkgb_val = self._dummy_pkg(test_dir, 'pkg-b')

            # prepare local sources mode
            init_config = dict(config)
            init_config.update({
                'local_sources': [
                    # --local-sources set with no paths
                    None,
                ],
            })

            with prepare_testenv(config=init_config) as engine:
                rv = engine.run()
                self.assertTrue(rv)
                self.assertTrue(os.path.exists(engine.opts.ff_local_srcs))

            # verify desired local sources are used
            with prepare_testenv(config=config) as engine:
                rv = engine.run()
                self.assertTrue(rv)

                target_dir = engine.opts.target_dir
                mdf_a = os.path.join(target_dir, 'metadata-a')
                mdf_b = os.path.join(target_dir, 'metadata-b')
                mdf_c = os.path.join(target_dir, 'metadata-c')
                self.assertTrue(os.path.exists(mdf_a))
                self.assertTrue(os.path.exists(mdf_b))
                self.assertTrue(os.path.exists(mdf_c))

                self._assertFileContains(mdf_a, pkga_val)
                self._assertFileContains(mdf_b, pkgb_val)
                self._assertFileContains(mdf_c, 'pkg-c-original')

                env_a = os.path.join(target_dir, 'invoke-env-a.json')
                env_b = os.path.join(target_dir, 'invoke-env-b.json')
                env_c = os.path.join(target_dir, 'invoke-env-c.json')
                self.assertTrue(os.path.exists(env_a))
                self.assertTrue(os.path.exists(env_b))
                self.assertTrue(os.path.exists(env_c))

                self._assertEnvLocalSrcs(env_a, True)
                self._assertEnvLocalSrcs(env_b, True)
                self._assertEnvLocalSrcs(env_c, False)

    def test_localsrcs_not_configured(self):
        with prepare_testenv(template='local-src') as engine:
            target_dir = engine.opts.target_dir

            rv = engine.run()
            self.assertTrue(rv)
            self.assertFalse(os.path.exists(engine.opts.ff_local_srcs))

            mdf_a = os.path.join(target_dir, 'metadata-a')
            mdf_b = os.path.join(target_dir, 'metadata-b')
            mdf_c = os.path.join(target_dir, 'metadata-c')
            self.assertTrue(os.path.exists(mdf_a))
            self.assertTrue(os.path.exists(mdf_b))
            self.assertTrue(os.path.exists(mdf_c))

            self._assertFileContains(mdf_a, 'pkg-a-original')
            self._assertFileContains(mdf_b, 'pkg-b-original')
            self._assertFileContains(mdf_c, 'pkg-c-original')

            env_a = os.path.join(target_dir, 'invoke-env-a.json')
            env_b = os.path.join(target_dir, 'invoke-env-b.json')
            env_c = os.path.join(target_dir, 'invoke-env-c.json')
            self.assertTrue(os.path.exists(env_a))
            self.assertTrue(os.path.exists(env_b))
            self.assertTrue(os.path.exists(env_c))

            self._assertEnvLocalSrcs(env_a, False)
            self._assertEnvLocalSrcs(env_b, False)
            self._assertEnvLocalSrcs(env_c, False)

    def test_localsrcs_overload_package(self):
        with workdir() as root_dir, workdir() as dir_a, workdir() as dir_b:
            config = {
                'root_dir': root_dir,
            }

            copy_template('local-src', root_dir)
            pkga_val = self._dummy_pkg(dir_a, 'pkg-a')
            pkgb_val = self._dummy_pkg(dir_b)

            # prepare local sources mode
            init_config = dict(config)
            init_config.update({
                'local_sources': [
                    # --local-sources set to a specific path
                    dir_a,
                    # overriding path for the `pkg-b` package
                    'pkg-b@{}'.format(dir_b),
                ],
            })

            with prepare_testenv(config=init_config) as engine:
                rv = engine.run()
                self.assertTrue(rv)
                self.assertTrue(os.path.exists(engine.opts.ff_local_srcs))

            # verify desired local sources are used
            with prepare_testenv(config=config) as engine:
                rv = engine.run()
                self.assertTrue(rv)

                target_dir = engine.opts.target_dir
                mdf_a = os.path.join(target_dir, 'metadata-a')
                mdf_b = os.path.join(target_dir, 'metadata-b')
                mdf_c = os.path.join(target_dir, 'metadata-c')
                self.assertTrue(os.path.exists(mdf_a))
                self.assertTrue(os.path.exists(mdf_b))
                self.assertTrue(os.path.exists(mdf_c))

                self._assertFileContains(mdf_a, pkga_val)
                self._assertFileContains(mdf_b, pkgb_val)
                self._assertFileContains(mdf_c, 'pkg-c-original')

                env_a = os.path.join(target_dir, 'invoke-env-a.json')
                env_b = os.path.join(target_dir, 'invoke-env-b.json')
                env_c = os.path.join(target_dir, 'invoke-env-c.json')
                self.assertTrue(os.path.exists(env_a))
                self.assertTrue(os.path.exists(env_b))
                self.assertTrue(os.path.exists(env_c))

                self._assertEnvLocalSrcs(env_a, True)
                self._assertEnvLocalSrcs(env_b, True)
                self._assertEnvLocalSrcs(env_c, False)

    def test_localsrcs_per_package(self):
        with workdir() as root_dir, workdir() as dir_a, workdir() as dir_b:
            config = {
                'root_dir': root_dir,
            }

            copy_template('local-src', root_dir)
            pkga_val = self._dummy_pkg(dir_a)
            pkgb_val = self._dummy_pkg(dir_b)

            # prepare local sources mode
            init_config = dict(config)
            init_config.update({
                'local_sources': [
                    # explicit path set for `pkg-a` package
                    'pkg-a@{}'.format(dir_a),
                    # explicit path set for `pkg-b` package
                    'pkg-b@{}'.format(dir_b),
                ],
            })

            with prepare_testenv(config=init_config) as engine:
                rv = engine.run()
                self.assertTrue(rv)
                self.assertTrue(os.path.exists(engine.opts.ff_local_srcs))

            # verify desired local sources are used
            with prepare_testenv(config=config) as engine:
                rv = engine.run()
                self.assertTrue(rv)

                target_dir = engine.opts.target_dir
                mdf_a = os.path.join(target_dir, 'metadata-a')
                mdf_b = os.path.join(target_dir, 'metadata-b')
                mdf_c = os.path.join(target_dir, 'metadata-c')
                self.assertTrue(os.path.exists(mdf_a))
                self.assertTrue(os.path.exists(mdf_b))
                self.assertTrue(os.path.exists(mdf_c))

                self._assertFileContains(mdf_a, pkga_val)
                self._assertFileContains(mdf_b, pkgb_val)
                self._assertFileContains(mdf_c, 'pkg-c-original')

                env_a = os.path.join(target_dir, 'invoke-env-a.json')
                env_b = os.path.join(target_dir, 'invoke-env-b.json')
                env_c = os.path.join(target_dir, 'invoke-env-c.json')
                self.assertTrue(os.path.exists(env_a))
                self.assertTrue(os.path.exists(env_b))
                self.assertTrue(os.path.exists(env_c))

                self._assertEnvLocalSrcs(env_a, True)
                self._assertEnvLocalSrcs(env_b, True)
                self._assertEnvLocalSrcs(env_c, False)

    def test_localsrcs_single_path(self):
        with workdir() as root_dir, workdir() as test_dir:
            config = {
                'root_dir': root_dir,
            }

            copy_template('local-src', root_dir)
            pkga_val = self._dummy_pkg(test_dir, 'pkg-a')
            pkgb_val = self._dummy_pkg(test_dir, 'pkg-b')

            # prepare local sources mode
            init_config = dict(config)
            init_config.update({
                'local_sources': [
                    # explicit path set
                    test_dir,
                ],
            })

            with prepare_testenv(config=init_config) as engine:
                rv = engine.run()
                self.assertTrue(rv)
                self.assertTrue(os.path.exists(engine.opts.ff_local_srcs))

            # verify desired local sources are used
            with prepare_testenv(config=config) as engine:
                rv = engine.run()
                self.assertTrue(rv)

                target_dir = engine.opts.target_dir
                mdf_a = os.path.join(target_dir, 'metadata-a')
                mdf_b = os.path.join(target_dir, 'metadata-b')
                mdf_c = os.path.join(target_dir, 'metadata-c')
                self.assertTrue(os.path.exists(mdf_a))
                self.assertTrue(os.path.exists(mdf_b))
                self.assertTrue(os.path.exists(mdf_c))

                self._assertFileContains(mdf_a, pkga_val)
                self._assertFileContains(mdf_b, pkgb_val)
                self._assertFileContains(mdf_c, 'pkg-c-original')

                env_a = os.path.join(target_dir, 'invoke-env-a.json')
                env_b = os.path.join(target_dir, 'invoke-env-b.json')
                env_c = os.path.join(target_dir, 'invoke-env-c.json')
                self.assertTrue(os.path.exists(env_a))
                self.assertTrue(os.path.exists(env_b))
                self.assertTrue(os.path.exists(env_c))

                self._assertEnvLocalSrcs(env_a, True)
                self._assertEnvLocalSrcs(env_b, True)
                self._assertEnvLocalSrcs(env_c, False)

    def test_localsrcs_specific_package(self):
        with workdir() as root_dir, workdir() as test_dir:
            config = {
                'root_dir': root_dir,
            }

            copy_template('local-src', root_dir)
            pkgb_val = self._dummy_pkg(test_dir)

            # prepare local sources mode
            init_config = dict(config)
            init_config.update({
                'local_sources': [
                    # explicit path set for a single package
                    'pkg-b@{}'.format(test_dir),
                ],
            })

            with prepare_testenv(config=init_config) as engine:
                rv = engine.run()
                self.assertTrue(rv)
                self.assertTrue(os.path.exists(engine.opts.ff_local_srcs))

            # verify desired local sources are used
            with prepare_testenv(config=config) as engine:
                rv = engine.run()
                self.assertTrue(rv)

                target_dir = engine.opts.target_dir
                mdf_a = os.path.join(target_dir, 'metadata-a')
                mdf_b = os.path.join(target_dir, 'metadata-b')
                mdf_c = os.path.join(target_dir, 'metadata-c')
                self.assertTrue(os.path.exists(mdf_a))
                self.assertTrue(os.path.exists(mdf_b))
                self.assertTrue(os.path.exists(mdf_c))

                self._assertFileContains(mdf_a, 'pkg-a-original')
                self._assertFileContains(mdf_b, pkgb_val)
                self._assertFileContains(mdf_c, 'pkg-c-original')

                env_a = os.path.join(target_dir, 'invoke-env-a.json')
                env_b = os.path.join(target_dir, 'invoke-env-b.json')
                env_c = os.path.join(target_dir, 'invoke-env-c.json')
                self.assertTrue(os.path.exists(env_a))
                self.assertTrue(os.path.exists(env_b))
                self.assertTrue(os.path.exists(env_c))

                self._assertEnvLocalSrcs(env_a, False)
                self._assertEnvLocalSrcs(env_b, True)
                self._assertEnvLocalSrcs(env_c, False)

    def test_localsrcs_unset_package(self):
        with workdir() as test_dir:
            root_dir = os.path.join(test_dir, 'root')

            config = {
                'root_dir': root_dir,
            }

            copy_template('local-src', root_dir)
            pkga_val = self._dummy_pkg(test_dir, 'pkg-a')

            # prepare local sources mode
            init_config = dict(config)
            init_config.update({
                'local_sources': [
                    # --local-sources set to a specific path
                    None,
                    # clearing path for the `pkg-b` package
                    'pkg-b@',
                ],
            })

            with prepare_testenv(config=init_config) as engine:
                rv = engine.run()
                self.assertTrue(rv)
                self.assertTrue(os.path.exists(engine.opts.ff_local_srcs))

            # verify desired local sources are used
            with prepare_testenv(config=config) as engine:
                rv = engine.run()
                self.assertTrue(rv)

                target_dir = engine.opts.target_dir
                mdf_a = os.path.join(target_dir, 'metadata-a')
                mdf_b = os.path.join(target_dir, 'metadata-b')
                mdf_c = os.path.join(target_dir, 'metadata-c')
                self.assertTrue(os.path.exists(mdf_a))
                self.assertTrue(os.path.exists(mdf_b))
                self.assertTrue(os.path.exists(mdf_c))

                self._assertFileContains(mdf_a, pkga_val)
                self._assertFileContains(mdf_b, 'pkg-b-original')
                self._assertFileContains(mdf_c, 'pkg-c-original')

                env_a = os.path.join(target_dir, 'invoke-env-a.json')
                env_b = os.path.join(target_dir, 'invoke-env-b.json')
                env_c = os.path.join(target_dir, 'invoke-env-c.json')
                self.assertTrue(os.path.exists(env_a))
                self.assertTrue(os.path.exists(env_b))
                self.assertTrue(os.path.exists(env_c))

                self._assertEnvLocalSrcs(env_a, True)
                self._assertEnvLocalSrcs(env_b, False)
                self._assertEnvLocalSrcs(env_c, False)

    def _dummy_pkg(self, container, pkg=None):
        uid = uuid.uuid4().hex

        if pkg:
            container = os.path.join(container, pkg)
        assert ensure_dir_exists(container)

        metadata = os.path.join(container, 'metadata')
        with open(metadata, 'w') as f:
            f.write(uid)

        return uid

    def _assertEnvLocalSrcs(self, path, expected):
        with open(path, 'r') as f:
            data = json.load(f)
            self.assertEqual('PKG_LOCALSRCS' in data, expected)

    def _assertFileContains(self, path, contents):
        with open(path, 'r') as f:
            data = f.read().strip()

        msg = 'found `{}` instead of `{}`'.format(data, contents)
        self.assertIn(contents, data, msg)
