===============================
nuage-openstack-neutronclient
===============================

"Openstack NeutronClient extensions for Nuage Networks"

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/nuage-openstack-neutron
* Source: http://git.openstack.org/cgit/openstack/nuage-openstack-neutron
* Bugs: http://bugs.launchpad.net/replace with the name of the project on launchpad

How to use
----------
To add a feature cli
* Create a class for your feature in nuage folder
* Import neutronclient.extension module from python-neutronclient
* Create a base class for your resource and inherit extension.NeutronClientExtension class
* Create classes for your cli's by inheriting from extension.ClientExtension<command name>, base class
* Add a entrypoint in setup.cfg as "resourcename = nuage.<resourceclassname>"
