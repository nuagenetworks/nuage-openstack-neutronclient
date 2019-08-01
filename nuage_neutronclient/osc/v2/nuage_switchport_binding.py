# Copyright 2019 NOKIA
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

from openstackclient.network import sdk_utils
from osc_lib.command import command
from osc_lib import utils
from osc_lib.utils import columns as column_util

from nuage_neutronclient._i18n import _

LOG = logging.getLogger(__name__)

RESOURCE_NAME = 'switchport_binding'
RESOURCE_NAME_PLURAL = 'switchport_bindings'


_attr_map = (('id', 'ID', column_util.LIST_BOTH),
             ('neutron_port_id', 'Neutron port ID', column_util.LIST_BOTH),
             ('switch_id', 'Switch ID', column_util.LIST_BOTH),
             ('port_id', 'Port ID', column_util.LIST_BOTH),
             ('segmentation_id', 'Segmentation ID', column_util.LIST_BOTH))


class ListNuageSwitchportBinding(command.Lister):
    """List Nuage Switchport Bindings"""

    def take_action(self, _):
        client = self.app.client_manager.nuageclient

        items = client.list_switchport_bindings()[RESOURCE_NAME_PLURAL]

        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=True)
        return (headers, (utils.get_dict_properties(obj, columns)
                          for obj in items))


class ShowNuageSwitchportBinding(command.ShowOne):
    """Show information of a given Nuage Switchport Binding"""

    def get_parser(self, prog_name):
        parser = super(ShowNuageSwitchportBinding, self).get_parser(prog_name)

        parser.add_argument(
            'nuage_switchport_binding',
            metavar='<nuage-switchport-binding>',
            help=_("Nuage switchport binding to display (ID)")
        )

        return parser

    def take_action(self, parsed_args):
        invisible_columns = ('tenant_id',)

        client = self.app.client_manager.nuageclient
        item = client.show_switchport_binding(
            parsed_args.nuage_switchport_binding)[RESOURCE_NAME]

        column_getter = sdk_utils.get_osc_show_columns_for_sdk_resource
        osc_column_map = {k: v for v, k, _ in _attr_map}
        columns, display_columns = column_getter(
            item, osc_column_map, invisible_columns)

        return display_columns, utils.get_dict_properties(item, columns)
