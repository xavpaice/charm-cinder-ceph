from mock import patch, call
import os
import cinder_utils as cinder_utils

from test_utils import (
    CharmTestCase,
)

TO_PATCH = [
    # helpers.core.hookenv
    'relation_ids',
    'service_name',
    # ceph utils
    'ceph_create_pool',
    'ceph_pool_exists',
    # storage_utils
    'get_os_codename_package',
    'templating',
    'install_alternative',
    'mkdir'
]


MOUNTS = [
    ['/mnt', '/dev/vdb']
]


class TestCinderUtils(CharmTestCase):

    def setUp(self):
        super(TestCinderUtils, self).setUp(cinder_utils, TO_PATCH)
        self.service_name.return_value = 'cinder-ceph'

    def test_ensure_ceph_pool(self):
        self.ceph_pool_exists.return_value = False
        cinder_utils.ensure_ceph_pool(service='cinder', replicas=3)
        self.ceph_create_pool.assert_called_with(service='cinder',
                                                 name='cinder',
                                                 replicas=3)

    def test_ensure_ceph_pool_already_exists(self):
        self.ceph_pool_exists.return_value = True
        cinder_utils.ensure_ceph_pool(service='cinder', replicas=3)
        self.assertFalse(self.ceph_create_pool.called)

    @patch('os.path.exists')
    def test_register_configs_ceph(self, exists):
        exists.return_value = True
        self.get_os_codename_package.return_value = 'grizzly'
        self.relation_ids.return_value = ['ceph:0']
        configs = cinder_utils.register_configs()
        calls = []
        for conf in [cinder_utils.ceph_config_file()]:
            calls.append(
                call(conf,
                     cinder_utils.CONFIG_FILES[conf]['hook_contexts'])
            )
        configs.register.assert_has_calls(calls, any_order=True)
        self.mkdir.assert_has_calls([
            call(os.path.dirname(cinder_utils.ceph_config_file())),
            call(os.path.dirname(cinder_utils.CEPH_CONF))
        ])
        self.install_alternative.assert_called_with(
            os.path.basename(cinder_utils.CEPH_CONF),
            cinder_utils.CEPH_CONF, cinder_utils.ceph_config_file()
        )

    def test_set_ceph_kludge(self):
        pass
        """
        def set_ceph_env_variables(service):
            # XXX: Horrid kludge to make cinder-volume use
            # a different ceph username than admin
            env = open('/etc/environment', 'r').read()
            if 'CEPH_ARGS' not in env:
                with open('/etc/environment', 'a') as out:
                    out.write('CEPH_ARGS="--id %s"\n' % service)
            with open('/etc/init/cinder-volume.override', 'w') as out:
                    out.write('env CEPH_ARGS="--id %s"\n' % service)
        """