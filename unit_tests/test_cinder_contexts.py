import cinder_contexts as contexts

from test_utils import (
    CharmTestCase
)

TO_PATCH = [
    'is_relation_made',
    'service_name',
]


class TestCinderContext(CharmTestCase):

    def setUp(self):
        super(TestCinderContext, self).setUp(contexts, TO_PATCH)

    def test_ceph_not_related(self):
        self.is_relation_made.return_value = False
        self.assertEquals(contexts.CephSubordinateContext()(), {})

    def test_ceph_related(self):
        self.is_relation_made.return_value = True
        service = 'mycinder'
        self.service_name.return_value = service
        self.assertEquals(
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
                        ]
                    }
                }
            }})
