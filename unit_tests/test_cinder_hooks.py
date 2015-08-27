from mock import MagicMock, patch
import json
import cinder_utils as utils

from test_utils import (
    CharmTestCase,
)

# Need to do some early patching to get the module loaded.
_register_configs = utils.register_configs
utils.register_configs = MagicMock()
import cinder_hooks as hooks
utils.register_configs = _register_configs

TO_PATCH = [
    # cinder_utils
    'ensure_ceph_keyring',
    'register_configs',
    'restart_map',
    'set_ceph_env_variables',
    'request_complete',
    'send_request_if_needed',
    'CONFIGS',
    # charmhelpers.core.hookenv
    'config',
    'relation_ids',
    'relation_set',
    'service_name',
    'service_restart',
    'log',
    # charmhelpers.core.host
    'apt_install',
    'apt_update',
    # charmhelpers.contrib.hahelpers.cluster_utils
    'execd_preinstall',
    'CephSubordinateContext',
    'delete_keyring'
]


class TestCinderHooks(CharmTestCase):
    def setUp(self):
        super(TestCinderHooks, self).setUp(hooks, TO_PATCH)
        self.config.side_effect = self.test_config.get

    @patch('charmhelpers.core.hookenv.config')
    def test_install(self, mock_config):
        hooks.hooks.execute(['hooks/install'])
        self.assertTrue(self.execd_preinstall.called)
        self.assertTrue(self.apt_update.called)
        self.apt_install.assert_called_with(['ceph-common'], fatal=True)

    @patch('charmhelpers.core.hookenv.config')
    @patch('os.mkdir')
    def test_ceph_joined(self, mkdir, mock_config):
        '''It correctly prepares for a ceph changed hook'''
        with patch('os.path.isdir') as isdir:
            isdir.return_value = False
            hooks.hooks.execute(['hooks/ceph-relation-joined'])
            mkdir.assert_called_with('/etc/ceph')

    @patch('charmhelpers.core.hookenv.config')
    def test_ceph_changed_no_key(self, mock_config):
        '''It does nothing when ceph key is not available'''
        self.CONFIGS.complete_contexts.return_value = ['']
        hooks.hooks.execute(['hooks/ceph-relation-changed'])
        m = 'ceph relation incomplete. Peer not ready?'
        self.log.assert_called_with(m)

    @patch('charmhelpers.core.hookenv.config')
    def test_ceph_changed(self, mock_config):
        '''It ensures ceph assets created on ceph changed'''
        self.request_complete.return_value = True
        self.CONFIGS.complete_contexts.return_value = ['ceph']
        self.service_name.return_value = 'cinder'
        self.ensure_ceph_keyring.return_value = True
        hooks.hooks.execute(['hooks/ceph-relation-changed'])
        self.ensure_ceph_keyring.assert_called_with(service='cinder',
                                                    user='cinder',
                                                    group='cinder')
        self.assertTrue(self.CONFIGS.write_all.called)
        self.set_ceph_env_variables.assert_called_with(service='cinder')

    @patch.object(hooks, 'get_ceph_request')
    @patch('charmhelpers.core.hookenv.config')
    def test_ceph_changed_newrq(self, mock_config, mock_get_ceph_request):
        '''It ensures ceph assets created on ceph changed'''
        mock_get_ceph_request.return_value = 'cephreq'
        self.request_complete.return_value = False
        self.CONFIGS.complete_contexts.return_value = ['ceph']
        self.service_name.return_value = 'cinder'
        self.ensure_ceph_keyring.return_value = True
        hooks.hooks.execute(['hooks/ceph-relation-changed'])
        self.ensure_ceph_keyring.assert_called_with(service='cinder',
                                                    user='cinder',
                                                    group='cinder')
        self.send_request_if_needed.assert_called_with('cephreq')

    @patch('charmhelpers.core.hookenv.config')
    def test_ceph_changed_no_keys(self, mock_config):
        '''It ensures ceph assets created on ceph changed'''
        self.CONFIGS.complete_contexts.return_value = ['ceph']
        self.service_name.return_value = 'cinder'
        self.request_complete.return_value = True
        self.ensure_ceph_keyring.return_value = False
        hooks.hooks.execute(['hooks/ceph-relation-changed'])
        # NOTE(jamespage): If ensure_ceph keyring fails, then
        # the hook should just exit 0 and return.
        self.assertTrue(self.log.called)
        self.assertFalse(self.CONFIGS.write_all.called)

    @patch('charmhelpers.core.hookenv.config')
    def test_ceph_broken(self, mock_config):
        self.CONFIGS.complete_contexts.return_value = ['ceph']
        self.service_name.return_value = 'cinder-ceph'
        hooks.hooks.execute(['hooks/ceph-relation-changed'])
        hooks.hooks.execute(['hooks/ceph-relation-broken'])
        self.delete_keyring.assert_called_with(service='cinder-ceph')
        self.assertTrue(self.CONFIGS.write_all.called)

    @patch('charmhelpers.core.hookenv.config')
    @patch.object(hooks, 'storage_backend')
    def test_upgrade_charm_related(self, _storage_backend, mock_config):
        self.CONFIGS.complete_contexts.return_value = ['ceph']
        self.relation_ids.return_value = ['ceph:1']
        hooks.hooks.execute(['hooks/upgrade-charm'])
        _storage_backend.assert_called_with('ceph:1')
        assert self.CONFIGS.write_all.called
        assert self.set_ceph_env_variables.called

    @patch('charmhelpers.core.hookenv.config')
    @patch.object(hooks, 'storage_backend')
    def test_storage_backend_changed(self, _storage_backend, mock_config):
        hooks.hooks.execute(['hooks/storage-backend-relation-changed'])
        _storage_backend.assert_called_with()

    @patch('charmhelpers.core.hookenv.config')
    def test_storage_backend_joined_no_ceph(self, mock_config):
        self.CONFIGS.complete_contexts.return_value = []
        hooks.hooks.execute(['hooks/storage-backend-relation-joined'])
        assert self.log.called
        assert not self.relation_set.called

    @patch('charmhelpers.core.hookenv.config')
    def test_storage_backend_joined_ceph(self, mock_config):
        def func():
            return {'test': 1}
        self.CONFIGS.complete_contexts.return_value = ['ceph']
        self.service_name.return_value = 'test'
        self.CephSubordinateContext.return_value = func
        hooks.hooks.execute(['hooks/storage-backend-relation-joined'])
        self.relation_set.assert_called_with(
            relation_id=None,
            backend_name='test',
            subordinate_configuration=json.dumps({'test': 1})
            )
