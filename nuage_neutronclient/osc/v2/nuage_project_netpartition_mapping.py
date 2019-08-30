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

from keystoneclient import utils as project_utils
from neutronclient.common import exceptions as neutron_exc
from osc_lib.command import command
from osc_lib import exceptions
from osc_lib import utils
from osc_lib.utils import columns as column_util

from nuage_neutronclient._i18n import _

LOG = logging.getLogger(__name__)

_attr_map = (('net_partition_name', 'Netpartition Name',
              column_util.LIST_LONG_ONLY),
             ('net_partition_id', 'Netpartition ID', column_util.LIST_BOTH),
             ('project', 'Associated Project', column_util.LIST_BOTH),
             )

RESOURCE_NAME = 'project_net_partition_mapping'
RESOURCE_PLURAL_NAME = 'project_net_partition_mappings'


class NuageProjectNetpartitionMapping(object):

    def _find_project_id(self, name_or_id):
        manager = self.app.client_manager.identity.projects
        return project_utils.find_resource(manager, name_or_id).id


class CreateNuageProjectNetpartitionMapping(NuageProjectNetpartitionMapping,
                                            command.ShowOne):
    """Create a new Nuage project netpartition mapping

        openstack nuage netpartition add project netpartition project
    """

    def get_parser(self, prog_name):
        parser = super(CreateNuageProjectNetpartitionMapping,
                       self).get_parser(prog_name)
        parser.add_argument(
            'net_partition', metavar='<netpartition>',
            help=_('ID or name of the netpartition to associate.'))
        parser.add_argument(
            'project', metavar='<project>',
            help=_('ID or name of the project'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        np = client.find_resource('net_partition',
                                  parsed_args.net_partition)
        project_id = self._find_project_id(parsed_args.project)
        body = {RESOURCE_NAME: {
            'project': project_id,
            'net_partition_id': np['id']
        }}
        item = client.create_project_netpartition_mapping(
            body)[RESOURCE_NAME]
        item['net_partition_name'] = np['name']

        columns, display_columns = column_util.get_columns(
            item, _attr_map)
        data = utils.get_dict_properties(
            item, columns)
        return display_columns, data


class DeleteNuageProjectNetpartitionMapping(NuageProjectNetpartitionMapping,
                                            command.Command):
    """Delete a given Nuage Project 2 Netpartition mapping"""

    def get_parser(self, prog_name):
        parser = super(DeleteNuageProjectNetpartitionMapping,
                       self).get_parser(prog_name)
        parser.add_argument(
            'project',
            metavar='<project>',
            nargs='+',
            help=_('Project to delete mapping for (name or ID)'))
        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        result = 0

        for project in parsed_args.project:
            try:
                project_id = self._find_project_id(project)
                client.delete_project_netpartition_mapping(project_id)
            except Exception as e:
                result += 1
                LOG.error(_("Failed netpartition remove project with "
                            "name or ID '{}': {}").format(project, e))

        if result > 0:
            total = len(parsed_args.nuage_netpartition)
            msg = (_("{result} of {total} nuage project to netpartition "
                     "mapping(s) failed to delete.").format(result=result,
                                                            total=total))
            raise exceptions.CommandError(msg)


class ListNuageProjectNetpartitionMapping(NuageProjectNetpartitionMapping,
                                          command.Lister):
    """List Nuage Netpartitions"""

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient

        mappings = client.list_project_netpartition_mappings()[
            RESOURCE_PLURAL_NAME]
        netpartitions = client.list_net_partitions()['net_partitions']
        netpartitions = {netpart['id']: netpart for netpart in netpartitions}
        for map in mappings:
            np = netpartitions[map['net_partition_id']]
            if np:
                map['net_partition_name'] = np['name']
        headers, columns = column_util.get_column_definitions(
            _attr_map, long_listing=True)
        return (headers, (utils.get_dict_properties(obj, columns)
                          for obj in mappings))


class ShowNuageProjectNetpartitionMapping(NuageProjectNetpartitionMapping,
                                          command.ShowOne):
    """Show information of a given Nuage Netpartition"""

    def get_parser(self, prog_name):
        parser = super(ShowNuageProjectNetpartitionMapping,
                       self).get_parser(prog_name)

        parser.add_argument(
            'project',
            metavar='<project>',
            help=_("Project to show mapping for (name or ID)")
        )

        return parser

    def take_action(self, parsed_args):
        client = self.app.client_manager.nuageclient
        project_id = self._find_project_id(parsed_args.project)
        try:
            obj = client.show_project_netpartition_mapping(
                project_id)[RESOURCE_NAME]
        except neutron_exc.NotFound:
            raise neutron_exc.NotFound('No Project netpartition '
                                       'mapping was found for Project '
                                       '{}.'.format(parsed_args.project))
        try:
            obj['net_partition_name'] = client.show_net_partition(
                obj['net_partition_id'])['net_partition']['name']
        except neutron_exc.NotFound:
            pass

        columns, display_columns = column_util.get_columns(obj, _attr_map)
        data = utils.get_dict_properties(obj, columns)
        return display_columns, data
