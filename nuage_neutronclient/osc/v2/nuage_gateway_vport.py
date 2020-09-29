# Copyright 2020 NOKIA
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
import logging

from keystoneclient import utils as keystone_utils
from osc_lib.command import command
from osc_lib import utils
from osc_lib.utils import columns as column_util

from nuage_neutronclient._i18n import _


LOG = logging.getLogger(__name__)

RESOURCE_NAME = 'nuage_gateway_vport'
RESOURCE_NAME_PLURAL = 'nuage_gateway_vports'


_attr_map = (('id', 'ID', column_util.LIST_BOTH),
             ('interface', 'Interface', column_util.LIST_BOTH),
             ('name', 'Name', column_util.LIST_BOTH),
             ('subnet', 'Subnet', column_util.LIST_BOTH),
             ('type', 'Type', column_util.LIST_BOTH),
             ('tenant_id', 'Tenant ID', column_util.LIST_LONG_ONLY),
             ('vlan', 'VLAN', column_util.LIST_LONG_ONLY),
             ('gateway', 'Gateway', column_util.LIST_LONG_ONLY),
             ('gatewayport', 'Gateway Port', column_util.LIST_LONG_ONLY),
             ('port', 'Port', column_util.LIST_LONG_ONLY),
             )


class CreateNuageGatewayVPort(command.ShowOne):
    """Create Nuage Gateway vPort"""

    def get_parser(self, prog_name):
        parser = super(CreateNuageGatewayVPort, self).get_parser(prog_name)
        parser.add_argument(
            'nuage_gateway_port_vlan_id',
            metavar='<nuage-gateway-port-vlan-id>',
            help=_("ID of nuage gateway port vlan"))
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--subnet', metavar='<subnet>',
            help=_("Openstack subnet (name or id). "
                   "Provide this argument in order to create a bridge port "
                   "in the provided neutron subnet."))
        group.add_argument(
            '--port',
            metavar='<port>',
            help=_("Openstack port (name or id). "
                   "Provide this argument in order to create a host port "
                   "based on the provided neutron port."))
        group.add_argument(
            '--project',
            metavar='<project>',
            help=_("Openstack project"))
        return parser

    def take_action(self, parsed_args):
        project_id = keystone_utils.find_resource(
            self.app.client_manager.identity.projects,
            parsed_args.project).id if parsed_args.project else ''

        body = {RESOURCE_NAME: {
            'gatewayvlan': parsed_args.nuage_gateway_port_vlan_id,
            'tenant': project_id
        }}

        if parsed_args.subnet:
            subnet_id = (self.app.client_manager.network
                         .find_subnet(parsed_args.subnet,
                                      ignore_missing=False).id)
            body[RESOURCE_NAME].update(subnet=subnet_id)
        if parsed_args.port:
            port_id = (self.app.client_manager.network
                       .find_port(parsed_args.port, ignore_missing=False).id)
            body[RESOURCE_NAME].update(port=port_id)

        client = self.app.client_manager.nuageclient
        item = client.create_nuage_gateway_vport(body)[RESOURCE_NAME]
        del item['tenant_id']

        columns, display_columns = column_util.get_columns(
            item, _attr_map)
        data = utils.get_dict_properties(
            item, columns)
        return display_columns, data


class DeleteNuageGatewayVPort(command.Command):
    """Delete Nuage Gateway vPort"""

    def get_parser(self, prog_name):
        parser = super(DeleteNuageGatewayVPort, self).get_parser(prog_name)
        parser.add_argument(
            'nuage_gateway_vport_id',
            metavar='<nuage-gateway-vport-id>',
            help=_("ID of the nuage gateway vPort"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        client.delete_nuage_gateway_vport(parsed_args.nuage_gateway_vport_id)


class ShowNuageGatewayVPort(command.ShowOne):
    """Show information of a given Nuage Gateway vPort"""

    def get_parser(self, prog_name):
        parser = super(ShowNuageGatewayVPort, self).get_parser(prog_name)
        parser.add_argument(
            'nuage_gateway_vport_id',
            metavar='<nuage-gateway-vport-id>',
            help=_("ID of the nuage gateway vPort"))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        obj = client.show_nuage_gateway_vport(
            parsed_args.nuage_gateway_vport_id)[RESOURCE_NAME]

        columns, display_columns = column_util.get_columns(obj, _attr_map)
        data = utils.get_dict_properties(obj, columns)
        return display_columns, data


class ListNuageGatewayVPort(command.Lister):
    """List Nuage Gateway vPort"""

    def get_parser(self, prog_name):
        parser = super(ListNuageGatewayVPort, self).get_parser(prog_name)
        parser.add_argument(
            'subnet', metavar='<subnet>',
            help=_('The openstack subnet (Name or ID)'))
        parser.add_argument(
            '--project', metavar='<nuage-project>',
            help=_('The owner project (Name or ID)'), default='')
        return parser

    def take_action(self, parsed_args):
        params = dict()
        if parsed_args.project:
            project_id = keystone_utils.find_resource(
                self.app.client_manager.identity.projects,
                parsed_args.project).id
            params.update(tenant=project_id)
        if parsed_args.subnet:
            subnet_id = self.app.client_manager.network.find_subnet(
                parsed_args.subnet, ignore_missing=False).id
            params.update(subnet=subnet_id)

        client = self.app.client_manager.nuageclient

        items = client.list_nuage_gateway_vports(
            **params)[RESOURCE_NAME_PLURAL]

        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=False)
        return (headers, (utils.get_dict_properties(obj, columns)
                          for obj in items))
