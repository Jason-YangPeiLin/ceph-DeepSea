# -*- coding: utf-8 -*-
# pylint: disable=C0111
# pylint: disable=import-error,3rd-party-module-not-gated,redefined-builtin

from __future__ import absolute_import

import logging

from salt.exceptions import CommandExecutionError


log = logging.getLogger(__name__)


def show_low_sls(*states):
    result = {}
    for state in states:
        if isinstance(state, dict):
            for key, states2 in state.items():
                res = {}
                for _ in states2:
                    res[state] = __salt__['state.show_low_sls'](state)
                result[key] = res
        else:
            result[state] = __salt__['state.show_low_sls'](state)
    return result


def user():
    """
    Returns the system user name for running the salt-master and own files
    """
    if __grains__.get('os_family', '') == 'Suse':
        return 'salt'
    return 'root'


def group():
    """
    Returns the system group name used for running the salt-master and own files
    """
    if __grains__.get('os_family', '') == 'Suse':
        return 'salt'
    return 'root'


def find_pool(applications, preferred_pool=None):
    try:
        import rados
    except ImportError:
        raise Exception("This method should not be called before Ceph is "
                        "installed")

    if not isinstance(applications, list):
        applications = [applications]

    cluster = rados.Rados(conffile="/etc/ceph/ceph.conf")
    cluster.connect()

    pools = [pool for pool in cluster.list_pools()]
    for pool in pools:
        if pool == preferred_pool:
            cluster.shutdown()
            return pool

    eligible_pools = []
    for pool in pools:
        pool_id = cluster.pool_lookup(pool)
        ioctx = cluster.open_ioctx(pool)
        for app in ioctx.application_list():
            if app in applications:
                eligible_pools.append((pool_id, pool))
        ioctx.close()

    cluster.shutdown()

    if not eligible_pools:
        return None

    eligible_pools = sorted(eligible_pools, key=lambda e: e[0])
    if [pool for _, pool in eligible_pools if pool == preferred_pool]:
        return preferred_pool
    return eligible_pools[0][1]


def ssl_ca_cert_cn():
    domain = __grains__['domain']
    if not domain:
        raise Exception("According to the 'domain' grain, the cluster does"
                        " not have a DNS domain configured")
    return "deepsea.{}".format(domain)


def ssl_cert_cn_wildcard():
    domain = __grains__['domain']
    if not domain:
        raise Exception("According to the 'domain' grain, the cluster does"
                        " not have a DNS domain configured")
    return "*.{}".format(domain)


def is_pkg_installed(pkg_name):
    try:
        result = __salt__['pkg.info_installed'](pkg_name)
    except CommandExecutionError as ex:
        log.info("%s is not installed? %s", pkg_name, str(ex))
        if str(ex).startswith('package {} is not'.format(pkg_name)):
            __context__['retcode'] = 0
            return {}

        return str(ex)
    log.info("Checking if %s is installed: %s", pkg_name, result)
    if isinstance(result, dict) and pkg_name in result:
        return result
    return {}
