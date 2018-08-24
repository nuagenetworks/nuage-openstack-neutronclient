#!/usr/bin/env bash

set -ex

# Note the actual url here is somewhat irrelevant because it
# caches in nodepool, however make it a valid url for
# documentation purposes.
export DEVSTACK_LOCAL_CONFIG="enable_plugin nuage-openstack-neutron git://git.openstack.org/openstack/nuage-openstack-neutron"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"enable_plugin nuage-openstack-neutronclient git://git.openstack.org/openstack/nuage-openstack-neutronclient"

export DEVSTACK_LOCAL_CONFIG+=$'\n'"NUAGE_FIP_UNDERLAY=True"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"OVS_BRIDGE=alubr0"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_USE_PROVIDERNET_FOR_PUBLIC=False"

# VSP related config
export DEVSTACK_LOCAL_CONFIG+=$'\n'"NUAGE_VSD_SERVERS=$VSD_SERVER"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"NUAGE_VSD_SERVER_AUTH=csproot:csproot"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"NUAGE_VSD_ORGANIZATION=csp"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"NUAGE_VSD_SERVER_SSL=True"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"NUAGE_VSD_AUTH_RESOURCE=/me"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"NUAGE_VSD_DEF_NETPART_NAME=DevstackCI-${ZUUL_CHANGE}-os-neutronclient-${RANDOM}"

# Keep localrc to be able to set some vars in pre_test_hook
export KEEP_LOCALRC=1

# Neutron Plugin related config
export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_PLUGIN=ml2"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_ML2_PLUGIN_EXT_DRIVERS=nuage_subnet,nuage_port,port_security,nuage_network"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_ML2_TENANT_NETWORK_TYPE=vxlan,vlan"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"ENABLE_TENANT_TUNNELS=True"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"ML2_VLAN_RANGES=physnet1:1:4000,physnet2:1:4000"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"PHYSICAL_NETWORK=physnet1,physnet2"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_ML2_PLUGIN_MECHANISM_DRIVERS=nuage,nuage_sriov,nuage_baremetal"
export DEVSTACK_LOCAL_CONFIG+=$'\n'"Q_ML2_PLUGIN_TYPE_DRIVERS=vxlan,vlan"

# disable neutron advanced services for nuage ci
export DEVSTACK_LOCAL_CONFIG+=$'\n'"disable_service q-lbaas q-fwaas q-vpn"

# We are only interested on Neutron and Heat, so very few services are needed
# to deploy devstack and run the tests
s=""
s+="mysql,rabbit"
s+=",key"
s+=",n-api,n-cond,n-cpu,n-crt,n-sch,placement-api"
s+=",g-api,g-reg"
s+=",q-svc,quantum"
s+=",dstat"

export OVERRIDE_ENABLED_SERVICES="$s"

export DEVSTACK_GATE_CONFIGDRIVE=1
export DEVSTACK_GATE_LIBVIRT_TYPE=kvm

# Explicitly set LOGDIR to align with the SCREEN_LOGDIR setting
# from devstack-gate.  Otherwise, devstack infers it from LOGFILE,
# which is not appropriate for our gate jobs.
export DEVSTACK_LOCAL_CONFIG+=$'\n'"LOGDIR=$BASE/new/screen-logs"

$BASE/new/devstack-gate/devstack-vm-gate.sh

