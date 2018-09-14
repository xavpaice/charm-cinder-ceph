# Copyright 2016 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import cinder_contexts as contexts

from test_utils import (
    CharmTestCase
)

TO_PATCH = [
    'is_relation_made',
    'service_name',
    'get_os_codename_package',
    'leader_get',
]


class TestCinderContext(CharmTestCase):

    def setUp(self):
        super(TestCinderContext, self).setUp(contexts, TO_PATCH)
        self.leader_get.return_value = 'libvirt-uuid'
        self.maxDiff = None

    def test_ceph_not_related(self):
        self.is_relation_made.return_value = False
        self.assertEqual(contexts.CephSubordinateContext()(), {})

    def test_ceph_related(self):
        self.is_relation_made.return_value = True
        self.get_os_codename_package.return_value = "havana"
        service = 'mycinder'
        self.service_name.return_value = service
        self.assertEqual(
            contexts.CephSubordinateContext()(),
            {"cinder": {
                "/etc/cinder/cinder.conf": {
                    "sections": {
                        service: [
                            ('volume_backend_name', service),
                            ('volume_driver',
                             'cinder.volume.driver.RBDDriver'),
                            ('rbd_pool', service),
                            ('rbd_user', service),
                            ('rbd_secret_uuid', 'libvirt-uuid'),
                            ('rbd_ceph_conf',
                             '/var/lib/charm/mycinder/ceph.conf')
                        ]
                    }
                }
            }})

    def test_ceph_related_icehouse(self):
        self.is_relation_made.return_value = True
        self.get_os_codename_package.return_value = "icehouse"
        service = 'mycinder'
        self.service_name.return_value = service
        self.assertEqual(
            contexts.CephSubordinateContext()(),
            {"cinder": {
                "/etc/cinder/cinder.conf": {
                    "sections": {
                        service: [
                            ('volume_backend_name', service),
                            ('volume_driver',
                             'cinder.volume.drivers.rbd.RBDDriver'),
                            ('rbd_pool', service),
                            ('rbd_user', service),
                            ('rbd_secret_uuid', 'libvirt-uuid'),
                            ('rbd_ceph_conf',
                             '/var/lib/charm/mycinder/ceph.conf')
                        ]
                    }
                }
            }})

    def test_ceph_related_queens(self):
        self.is_relation_made.return_value = True
        self.get_os_codename_package.return_value = "queens"
        service = 'mycinder'
        self.service_name.return_value = service
        self.assertEqual(
            contexts.CephSubordinateContext()(),
            {"cinder": {
                "/etc/cinder/cinder.conf": {
                    "sections": {
                        service: [
                            ('volume_backend_name', service),
                            ('volume_driver',
                             'cinder.volume.drivers.rbd.RBDDriver'),
                            ('rbd_pool', service),
                            ('rbd_user', service),
                            ('rbd_secret_uuid', 'libvirt-uuid'),
                            ('rbd_ceph_conf',
                             '/var/lib/charm/mycinder/ceph.conf'),
                            ('rbd_exclusive_cinder_pool', True)
                        ]
                    }
                }
            }})
