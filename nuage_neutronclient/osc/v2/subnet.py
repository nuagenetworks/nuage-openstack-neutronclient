# Copyright 2016 NEC Corporation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from neutronclient.common import utils
from nuage_neutronclient.osc.v2.utils import update_dict
from openstack.network.v2.subnet import Subnet as subnet_resource
from openstack import resource
from openstackclient.i18n import _
from openstackclient.network.v2 import subnet
from osc_lib import exceptions

openstack_get_attrs = subnet._get_attrs

# Add Nuage specific attributes to Openstack Subnet
subnet_resource.net_partition = resource.Body('net_partition')
subnet_resource.nuagenet = resource.Body('nuagenet')
subnet_resource.nuage_uplink = resource.Body('nuage_uplink')
subnet_resource.nuage_underlay = resource.Body('nuage_underlay')
subnet_resource.underlay = resource.Body('underlay', type=bool)
subnet_resource.vsd_managed = resource.Body('vsd_managed', type=bool)


def nuage_get_attrs(client_manager, parsed_args, is_create=True):
    attrs = openstack_get_attrs(client_manager, parsed_args, is_create)

    if (hasattr(parsed_args, "nuagenet") and
            hasattr(parsed_args, "net_partition") and
            parsed_args.nuagenet is not None and
            parsed_args.net_partition is None):
        msg = _("'nuagenet' and 'net_partition' parameters should both be "
                "given for creating a vsd-managed subnet.")
        raise exceptions.CommandError(msg)

    update_dict(parsed_args, attrs,
                ['net_partition', 'nuagenet', 'nuage_uplink', 'nuage_underlay',
                 'underlay'])

    return attrs


subnet._get_attrs = nuage_get_attrs


class CreateSubnet(subnet.CreateSubnet):

    def get_parser(self, prog_name):
        parser = super(CreateSubnet, self).get_parser(prog_name)
        parser.add_argument(
            '--net-partition',
            help=_('ID or name of the net partition.'))
        parser.add_argument(
            '--nuagenet',
            help=_('ID of the subnet or l2domain on the VSD.'))
        parser.add_argument(
            '--nuage-uplink',
            help=_('ID of the shared resource zone on the VSD.'))
        utils.add_boolean_argument(
            parser, '--underlay',
            help=_('Whether to enable or disable underlay for shared '
                   'networks'))
        return parser


class SetSubnet(subnet.SetSubnet):

    def get_parser(self, prog_name):
        parser = super(SetSubnet, self).get_parser(prog_name)
        parser.add_argument(
            '--nuage-underlay',
            type=utils.convert_to_lowercase,
            choices=['off', 'route', 'snat', 'inherited'],
            help=_('Enable nuage underlay options.'))
        return parser


class ShowSubnet(subnet.ShowSubnet):
    pass
