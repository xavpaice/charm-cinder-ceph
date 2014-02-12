import os
from collections import OrderedDict

from charmhelpers.core.hookenv import (
    relation_ids,
    service_name,
)

from charmhelpers.contrib.storage.linux.ceph import (
    create_pool as ceph_create_pool,
    pool_exists as ceph_pool_exists,
)

from charmhelpers.contrib.openstack import (
    templating,
    context,
)

from charmhelpers.contrib.openstack.utils import (
    get_os_codename_package,
)

from charmhelpers.contrib.openstack.alternatives import install_alternative
from charmhelpers.core.host import mkdir


PACKAGES = [
    'ceph-common',
]

CHARM_CEPH_CONF = '/var/lib/charm/{}/ceph.conf'
CEPH_CONF = '/etc/ceph/ceph.conf'

TEMPLATES = 'templates/'

# Map config files to hook contexts and services that will be associated
# with file in restart_on_changes()'s service map.
CONFIG_FILES = {}


def ceph_config_file():
    return CHARM_CEPH_CONF.format(service_name())


def register_configs():
    """
    Register config files with their respective contexts.
    Regstration of some configs may not be required depending on
    existing of certain relations.
    """
    # if called without anything installed (eg during install hook)
    # just default to earliest supported release. configs dont get touched
    # till post-install, anyway.
    release = get_os_codename_package('cinder-common', fatal=False) or 'folsom'
    configs = templating.OSConfigRenderer(templates_dir=TEMPLATES,
                                          openstack_release=release)

    confs = []

    if relation_ids('ceph'):
        # Add charm ceph configuration to resources and
        # ensure directory actually exists
        mkdir(os.path.dirname(ceph_config_file()))
        mkdir(os.path.dirname(CEPH_CONF))
        # Install ceph config as an alternative for co-location with
        # ceph and ceph-osd charms - nova-compute ceph.conf will be
        # lower priority that both of these but thats OK
        if not os.path.exists(ceph_config_file()):
            # touch file for pre-templated generation
            open(ceph_config_file(), 'w').close()
        install_alternative(os.path.basename(CEPH_CONF),
                            CEPH_CONF, ceph_config_file())
        CONFIG_FILES[ceph_config_file()] = {
            'hook_contexts': [context.CephContext()],
            'services': ['cinder-volume'],
        }
        confs.append(ceph_config_file())

    for conf in confs:
        configs.register(conf, CONFIG_FILES[conf]['hook_contexts'])

    return configs


def restart_map():
    '''
    Determine the correct resource map to be passed to
    charmhelpers.core.restart_on_change() based on the services configured.

    :returns: dict: A dictionary mapping config file to lists of services
                    that should be restarted when file changes.
    '''
    _map = []
    for f, ctxt in CONFIG_FILES.iteritems():
        svcs = []
        for svc in ctxt['services']:
            svcs.append(svc)
        if svcs:
            _map.append((f, svcs))
    return OrderedDict(_map)


def ensure_ceph_pool(service, replicas):
    '''Creates a ceph pool for service if one does not exist'''
    # TODO: Ditto about moving somewhere sharable.
    if not ceph_pool_exists(service=service, name=service):
        ceph_create_pool(service=service, name=service, replicas=replicas)


def set_ceph_env_variables(service):
    # XXX: Horrid kludge to make cinder-volume use
    # a different ceph username than admin
    env = open('/etc/environment', 'r').read()
    if 'CEPH_ARGS' not in env:
        with open('/etc/environment', 'a') as out:
            out.write('CEPH_ARGS="--id %s"\n' % service)
    with open('/etc/init/cinder-volume.override', 'w') as out:
            out.write('env CEPH_ARGS="--id %s"\n' % service)
