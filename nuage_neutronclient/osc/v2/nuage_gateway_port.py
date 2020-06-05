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

from osc_lib.command import command
from osc_lib import utils
from osc_lib.utils import columns as column_util

from nuage_neutronclient._i18n import _
from nuage_neutronclient.osc.v2.nuage_gateway \
    import RESOURCE_NAME as GW_RESOURCE_NAME
from nuage_neutronclient.osc.v2.utils import find_nested_resource

LOG = logging.getLogger(__name__)

RESOURCE_NAME = 'nuage_gateway_port'
RESOURCE_NAME_PLURAL = 'nuage_gateway_ports'

_attr_map = (('id', 'ID', column_util.LIST_BOTH),
             ('usermnemonic', 'User mnemonic', column_util.LIST_BOTH),
             ('physicalname', 'Physical name', column_util.LIST_BOTH),
             ('vlan', 'VLAN', column_util.LIST_BOTH),
             ('tenant_id', 'Tenant ID', column_util.LIST_BOTH),
             ('name', 'Name', column_util.LIST_BOTH),
             ('status', 'Status', column_util.LIST_BOTH),
             )


class ListNuageGatewayPort(command.Lister):
    """List Nuage Gateway Port"""

    def get_parser(self, prog_name):
        parser = super(ListNuageGatewayPort, self).get_parser(prog_name)
        parser.add_argument(
            'nuage_gateway',
            metavar='<nuage-gateway>',
            help=_("Nuage gateway for which to list ports (name or ID)")
        )

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        gw_id = client.find_resource(GW_RESOURCE_NAME,
                                     parsed_args.nuage_gateway)['id']

        items = client.list_nuage_gateway_ports(
            gateway=gw_id)[RESOURCE_NAME_PLURAL]

        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=False)
        return (headers, (utils.get_dict_properties(obj, columns)
                          for obj in items))


class ShowNuageGatewayPort(command.ShowOne):
    """Show information of a given Nuage Gateway Port"""

    def get_parser(self, prog_name):
        parser = super(ShowNuageGatewayPort, self).get_parser(prog_name)
        parser.add_argument(
            'nuage_gateway_port',
            metavar='<nuage-gateway-port>',
            help=_("Nuage gateway port to display "
                   "(ID or name if --gateway is also provided)")
        )
        parser.add_argument(
            '--gateway',
            metavar='<nuage-gateway>',
            help=_("Nuage gateway the port belongs to (name or ID). "
                   "Provide this argument in order to search by port name.")
        )

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient

        obj = find_nested_resource(
            name_or_id=parsed_args.nuage_gateway_port,
            parent_name_or_id=parsed_args.gateway,
            resource_finder=(
                lambda x: client.show_nuage_gateway_port(x)[RESOURCE_NAME]),
            resource_lister=(
                lambda **kwargs: client.list_nuage_gateway_ports(
                    **kwargs)[RESOURCE_NAME_PLURAL]),
            parent_resource_finder=(
                lambda x: client.find_resource(GW_RESOURCE_NAME, x)),
            resource_name='gatewayport',
            parent_resource_name='gateway'
        )

        columns, display_columns = column_util.get_columns(obj, _attr_map)
        data = utils.get_dict_properties(obj, columns)
        return display_columns, data
