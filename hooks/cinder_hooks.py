#!/usr/bin/python

import os
import sys
import json

from cinder_utils import (
    register_configs,
    restart_map,
    set_ceph_env_variables,
    PACKAGES
)
from cinder_contexts import CephSubordinateContext

from charmhelpers.core.host import (
    service_restart,
)

from charmhelpers.core.hookenv import (
    Hooks,
    UnregisteredHookError,
    config,
    service_name,
    relation_get,
    relation_set,
    relation_ids,
    log,
    INFO,
    ERROR,
)
from charmhelpers.fetch import apt_install, apt_update
from charmhelpers.core.host import restart_on_change
from charmhelpers.contrib.storage.linux.ceph import (
    ensure_ceph_keyring,
    CephBrokerRq,
    CephBrokerRsp,
    delete_keyring,
)
from charmhelpers.payload.execd import execd_preinstall

hooks = Hooks()

CONFIGS = register_configs()


@hooks.hook('install')
def install():
    execd_preinstall()
    apt_update(fatal=True)
    apt_install(PACKAGES, fatal=True)


@hooks.hook('ceph-relation-joined')
def ceph_joined():
    if not os.path.isdir('/etc/ceph'):
        os.mkdir('/etc/ceph')


@hooks.hook('ceph-relation-changed')
@restart_on_change(restart_map())
def ceph_changed():
    if 'ceph' not in CONFIGS.complete_contexts():
        log('ceph relation incomplete. Peer not ready?')
        return

    service = service_name()
    if not ensure_ceph_keyring(service=service,
                               user='cinder', group='cinder'):
        log('Could not create ceph keyring: peer not ready?')
        return

    settings = relation_get()
    if settings and 'broker_rsp' in settings:
        rsp = CephBrokerRsp(settings['broker_rsp'])
        # Non-zero return code implies failure
        if rsp.exit_code:
            log("Ceph broker request failed (rc=%s, msg=%s)" %
                (rsp.exit_code, rsp.exit_msg), level=ERROR)
            return

        log("Ceph broker request succeeded (rc=%s, msg=%s)" %
            (rsp.exit_code, rsp.exit_msg), level=INFO)
        CONFIGS.write_all()
        set_ceph_env_variables(service=service)
        for rid in relation_ids('storage-backend'):
            storage_backend(rid)

        # Ensure that cinder-volume is restarted since only now can we
        # guarantee that ceph resources are ready.
        service_restart('cinder-volume')
    else:
        rq = CephBrokerRq()
        replicas = config('ceph-osd-replication-count')
        rq.add_op_create_pool(name=service, replica_count=replicas)
        for rid in relation_ids('ceph'):
            relation_set(relation_id=rid, broker_req=rq.request)
            log("Request(s) sent to Ceph broker (rid=%s)" % (rid))


@hooks.hook('ceph-relation-broken')
def ceph_broken():
    service = service_name()
    delete_keyring(service=service)
    CONFIGS.write_all()


@hooks.hook('config-changed')
@restart_on_change(restart_map())
def write_and_restart():
    CONFIGS.write_all()


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


@hooks.hook('storage-backend-relation-changed')
def storage_backend_changed():
    # NOTE(jamespage) recall storage_backend as this only ever
    # changes post initial creation if the cinder charm is upgraded to a new
    # version of openstack.
    storage_backend()


@hooks.hook('upgrade-charm')
@restart_on_change(restart_map())
def upgrade_charm():
    if 'ceph' in CONFIGS.complete_contexts():
        CONFIGS.write_all()
        set_ceph_env_variables(service=service_name())
        for rid in relation_ids('storage-backend'):
            storage_backend(rid)


if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))
