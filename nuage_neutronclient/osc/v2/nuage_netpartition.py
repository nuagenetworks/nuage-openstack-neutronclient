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
from osc_lib import exceptions
from osc_lib import utils
from osc_lib.utils import columns as column_util

from nuage_neutronclient._i18n import _

LOG = logging.getLogger(__name__)

_attr_map = (('id', 'ID', column_util.LIST_BOTH),
             ('name', 'Name', column_util.LIST_BOTH),
             )


class CreateNuageNetpartition(command.ShowOne):
    """Create a new Nuage netpartition"""

    def get_parser(self, prog_name):
        parser = super(CreateNuageNetpartition, self).get_parser(prog_name)

        parser.add_argument(
            'name',
            metavar='<name>',
            help=_("New netparition name")
        )

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        item = client.create_net_partition(
            name=parsed_args.name)['net_partition']

        column_getter = sdk_utils.get_osc_show_columns_for_sdk_resource
        osc_column_map = {k: v for v, k, _ in _attr_map}
        columns, display_columns = column_getter(
            item, osc_column_map)

        return display_columns, utils.get_dict_properties(item, columns)


class DeleteNuageNetpartition(command.Command):
    """Delete a given Nuage Netpartition"""

    def get_parser(self, prog_name):
        parser = super(DeleteNuageNetpartition, self).get_parser(prog_name)
        parser.add_argument(
            'nuage_netpartition',
            metavar='<nuage-netpartition>',
            nargs='+',
            help=_('Nuage Netpartitions to delete (name or ID)'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        result = 0

        # TODO() Upstream contribution idea: below code is standard for delete
        # ..and copied throughout all resources upstream and downstream
        for netpartition in parsed_args.nuage_netpartition:
            try:
                netpartition_id = client.find_net_partition(
                    name_or_id=netpartition)['id']
                client.delete_net_partition(netpartition_id)
            except Exception as e:
                result += 1
                LOG.error(_("Failed to delete nuage netpartition with "
                            "name or ID '{}': {}").format(netpartition, e))

        if result > 0:
            total = len(parsed_args.nuage_netpartition)
            msg = (_("{result} of {total} nuage netpartition(s) failed "
                     "to delete.").format(result=result, total=total))
            raise exceptions.CommandError(msg)


class ListNuageNetpartition(command.Lister):
    """List Nuage Netpartitions"""

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient

        net_partitions = client.list_net_partitions()['net_partitions']

        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=True)
        return (headers, (utils.get_dict_properties(obj, columns)
                          for obj in net_partitions))


class ShowNuageNetPartition(command.ShowOne):
    """Show information of a given Nuage Netpartition"""

    def get_parser(self, prog_name):
        parser = super(ShowNuageNetPartition, self).get_parser(prog_name)

        parser.add_argument(
            'nuage_netpartition',
            metavar='<nuage-netpartition>',
            help=_("Nuage netpartition to display (name or ID)")
        )

        return parser

    def take_action(self, parsed_args):
        # Hide tenant_id for now, the value incorrect in the
        # plugin implementation
        invisible_columns = ('tenant_id',)

        client = self.app.client_manager.nuageclient
        # At this time client.find_resource is implemented using list instead
        # of show, that's why we have to do two calls. Once this is fixed
        # upstream we can reduce the number of calls
        netpartition_id = client.find_net_partition(
            name_or_id=parsed_args.nuage_netpartition)['id']
        item = client.show_net_partition(netpartition_id)['net_partition']

        column_getter = sdk_utils.get_osc_show_columns_for_sdk_resource
        osc_column_map = {k: v for v, k, _ in _attr_map}
        columns, display_columns = column_getter(
            item, osc_column_map, invisible_columns)

        return display_columns, utils.get_dict_properties(item, columns)
