from charmhelpers.core.hookenv import (
    service_name,
    is_relation_made
)

from charmhelpers.contrib.openstack.context import (
    OSContextGenerator,
)


class CephSubordinateContext(OSContextGenerator):
    interfaces = ['ceph-cinder']

    def __call__(self):
        """
        Used to generate template context to be added to cinder.conf in the
        presence of a ceph relation.
        """
        if not is_relation_made('ceph', 'key'):
            return {}
        service = service_name()
        return {
            "cinder": {
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
            }
        }
