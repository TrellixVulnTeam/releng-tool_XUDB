# -*- coding: utf-8 -*-
# Copyright 2018-2021 releng-tool

from releng_tool.tool.scp import SCP
from releng_tool.util.log import err
from releng_tool.util.log import log
from releng_tool.util.log import note
import sys


def fetch(opts):
    """
    support fetching from scp sources

    With provided fetch options (``RelengFetchOptions``), the fetch stage will
    be processed.

    Args:
        opts: fetch options

    Returns:
        ``True`` if the fetch stage is completed; ``False`` otherwise
    """

    assert opts
    cache_file = opts.cache_file
    name = opts.name
    site = opts.site
    work_dir = opts.work_dir

    if not SCP.exists():
        err('unable to fetch package; scp is not installed')
        return None

    note('fetching {}...', name)
    sys.stdout.flush()

    if not SCP.execute(['-o', 'BatchMode yes', site, cache_file], cwd=work_dir):
        err('unable to secure-copied file from target')
        return None
    log('successfully secure-copied file from target')

    return cache_file
