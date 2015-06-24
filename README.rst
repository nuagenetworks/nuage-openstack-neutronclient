===============================
nuage-openstack-neutronclient
===============================

"Openstack NeutronClient extensions for Nuage Networks"

* Free software: Apache license
* Source: http://github.com/nuagenetworks/openstack/nuage-openstack-neutron

=====================
End Users: How to Use
=====================

NeutronClient extensions using Client command extension support introduced in
https://review.openstack.org/#/c/148318/ in python-neutronclient 2.4.0 and above.

This provides the following extensions:

* Application Designer
* Gateway
* Redirect Target

======================
Developers: How to Use
======================

* Create a class for your feature in nuage_neutronclient folder
* Import neutronclient.extension module from python-neutronclient
* Create a base class for your resource and inherit extension.NeutronClientExtension class
* Create classes for your cli's by inheriting from extension.ClientExtension<command name>,
  base class
* Add a entrypoint in setup.cfg as "resourcename = nuage_neutronclient.<resourceclassname>"
