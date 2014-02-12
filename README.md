Ceph Storage Backend for Cinder
-------------------------------

Overview
========

This charm provides a Ceph storage backend for use with the Cinder
charm; this allows multiple Ceph storage clusters to be associated
with a single Cinder deployment, potentially alongside other storage
backends from other vendors.

To use:

    juju deploy cinder
    juju deploy -n 3 ceph
    juju deploy cinder-ceph
    juju add-relation cinder-ceph cinder
    juju add-relation cinder-ceph ceph

Configuration
=============

The cinder-ceph charm allows the replica count for the Ceph storage
pool to be configured.  This must be done in advance of relating to
the ceph charm:

    juju set cinder-ceph ceph-osd-replication-count=3
    juju add-relation cinder-ceph ceph

By default, the replica count is set to 2 replicas. Increasing this
value increases data resilience at the cost of consuming most real
storage in the Ceph cluster.

