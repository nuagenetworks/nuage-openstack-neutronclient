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
To add a feature
1. Create a class for your feature in nuage folder
2. Import neutronclient.extension module from python-neutronclient
3. Create a base class for your resource and inherit extension.NeutronClientExtension class
4. Create classes for your cli's and inherit from extension.ClientExtension<command name>, 
   resource base class
5. Add a entrypoint in setup.cfg as "resourcename = nuage.<resourceclassname>"
