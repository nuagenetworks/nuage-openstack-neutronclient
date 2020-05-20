#!/bin/bash
# plugin.sh - DevStack plugin.sh dispatch script

DIR_NUAGECLIENT=$DEST/nuage-openstack-neutronclient

function install_nuage_neutronclient {
     setup_develop $DIR_NUAGECLIENT
}


# check for service enabled
if is_service_enabled nuage_neutronclient; then

    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        # Perform installation of service source
        echo_summary "Installing nuage-neutronclient"
        install_nuage_neutronclient
    fi

    if [[ "$1" == "unstack" ]]; then
        # no-op
        :
    fi

    if [[ "$1" == "clean" ]]; then
        # Remove state and transient data
        # Remember clean.sh first calls unstack.sh
        # no-op
        :
    fi
fi
