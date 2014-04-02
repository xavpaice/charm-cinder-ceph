from charmhelpers.core.hookenv import (
    service_name,
    is_relation_made,
    config
)

from charmhelpers.contrib.openstack.context import (
    OSContextGenerator,
)

from charmhelpers.contrib.openstack.utils import get_os_codename_install_source


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
        if get_os_codename_install_source(config('openstack-origin')) \
                >= "icehouse":
            volume_driver = 'cinder.volume.drivers.rbd.RBDDriver'
        else:
            volume_driver = 'cinder.volume.driver.RBDDriver'
        return {
            "cinder": {
                "/etc/cinder/cinder.conf": {
                    "sections": {
                        service: [
                            ('volume_backend_name', service),
                            ('volume_driver', volume_driver),
                            ('rbd_pool', service),
                            ('rbd_user', service),
                        ]
                    }
                }
            }
        }
