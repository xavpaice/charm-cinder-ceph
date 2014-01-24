#!/usr/bin/python

import os
import sys
import json

from cinder_utils import (
    ensure_ceph_pool,
    register_configs,
    restart_map,
    set_ceph_env_variables,
    CEPH_CONF,
    PACKAGES
)

from charmhelpers.core.hookenv import (
    Hooks,
    UnregisteredHookError,
    config,
    service_name,
    relation_set,
    relation_ids
)

from cinder_contexts import CephSubordinateContext

from charmhelpers.fetch import apt_install, apt_update
from charmhelpers.core.host import restart_on_change, log

from charmhelpers.contrib.storage.linux.ceph import ensure_ceph_keyring
from charmhelpers.contrib.hahelpers.cluster import eligible_leader

from charmhelpers.payload.execd import execd_preinstall

hooks = Hooks()

CONFIGS = register_configs()


@hooks.hook('install')
def install():
    execd_preinstall()
    apt_update()
    apt_install(PACKAGES, fatal=True)


@hooks.hook('config-changed')
def config_changed():
    CONFIGS.write_all()


@hooks.hook('ceph-relation-joined')
def ceph_joined():
    if not os.path.isdir('/etc/ceph'):
        os.mkdir('/etc/ceph')


@hooks.hook('ceph-relation-changed')
@restart_on_change(restart_map())
def ceph_changed():
    if 'ceph' not in CONFIGS.complete_contexts():
        log('ceph relation incomplete. Peer not ready?')
    else:
        svc = service_name()
        if not ensure_ceph_keyring(service=svc,
                                   user='cinder', group='cinder'):
            log('Could not create ceph keyring: peer not ready?')
        else:
            CONFIGS.write(CEPH_CONF)
            set_ceph_env_variables(service=svc)
            if eligible_leader(None):
                ensure_ceph_pool(service=svc,
                                 replicas=config('ceph-osd-replication-count'))
            for rid in relation_ids('storage-backend'):
                storage_backend(rid)


@hooks.hook('ceph-relation-broken')
@restart_on_change(restart_map())
def relation_broken():
    CONFIGS.write_all()


@hooks.hook('upgrade-charm')
def upgrade_charm():
    pass


@hooks.hook('storage-backend-relation-joined')
def storage_backend(rel_id=None):
    if 'ceph' not in CONFIGS.complete_contexts():
        log('ceph relation incomplete. Peer not ready?')
    else:
        relation_set(
            relation_id=rel_id,
            backend_name=service_name(),
            subordinate_configuration=json.dumps(CephSubordinateContext()())
        )


if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))
