# -*- coding: utf-8 -*-
# Copyright 2018 releng-tool

def releng_setup(app):
    seed_ext_type = RelengSeedExtension
    app.add_fetch_type('ext-seed', seed_ext_type)
    app.add_extract_type('ext-seed', seed_ext_type)
    app.add_package_type('ext-seed', seed_ext_type)


class RelengSeedExtension:
    def fetch(self, name, opts):
        print('(seed) package', opts.name, 'has been fetched')

        try:
            open(opts.cache_file, 'w').close()
            return opts.cache_file
        except IOError:
            return None

    def extract(self, name, opts):
        print('(seed) package', opts.name, 'has been extracted')
        return True

    def configure(self, name, opts):
        print('(seed) package', opts.name, 'has been configured')
        return True

    def build(self, name, opts):
        print('(seed) package', opts.name, 'has been built')
        return True

    def install(self, name, opts):
        print('(seed) package', opts.name, 'has been installed')
        return True
