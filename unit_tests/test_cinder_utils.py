from mock import patch, call
import cinder_utils as cinder_utils

from test_utils import (
    CharmTestCase,
)

TO_PATCH = [
    # helpers.core.hookenv
    'relation_ids',
    # ceph utils
    'ceph_create_pool',
    'ceph_pool_exists',
    # storage_utils
    'get_os_codename_package',
    'templating',
]


MOUNTS = [
    ['/mnt', '/dev/vdb']
]


class TestCinderUtils(CharmTestCase):

    def setUp(self):
        super(TestCinderUtils, self).setUp(cinder_utils, TO_PATCH)

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

    @patch('os.mkdir')
    @patch('os.path.isdir')
    @patch('os.path.exists')
    def test_register_configs_ceph(self, exists, isdir, mkdir):
        exists.return_value = False
        isdir.return_value = False
        self.get_os_codename_package.return_value = 'grizzly'
        self.relation_ids.return_value = ['ceph:0']
        configs = cinder_utils.register_configs()
        calls = []
        for conf in [cinder_utils.CEPH_CONF]:
            calls.append(
                call(conf,
                     cinder_utils.CONFIG_FILES[conf]['hook_contexts'])
            )
        configs.register.assert_has_calls(calls, any_order=True)
        self.assertTrue(mkdir.called)

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
