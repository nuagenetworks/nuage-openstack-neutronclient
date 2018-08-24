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

from openstack.network.v2.security_group import SecurityGroup
from openstack import resource
from openstackclient.network import sdk_utils
from openstackclient.network.v2 import security_group

from nuage_neutronclient._i18n import _

# Add Nuage specific attributes
SecurityGroup.stateful = resource.Body('stateful', type=bool)


def add_create_update_attributes(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--stateful', action='store_true',
                       help=_('Specify that the security group is stateful.'))
    group.add_argument('--no-stateful', action='store_true',
                       help=_('Specify that the security group is not '
                              'stateful.'))


def get_nuage_attrs(parsed_args):
    attrs = {}

    if parsed_args.stateful or parsed_args.no_stateful:
        attrs['stateful'] = parsed_args.stateful

    return attrs


def _get_columns(item):
    column_map = {
        'security_group_rules': 'rules',
        'tenant_id': 'project_id',
        'stateful': 'stateful'
    }
    return sdk_utils.get_osc_show_columns_for_sdk_resource(item, column_map)


security_group._get_columns = _get_columns


class CreateSecurityGroup(security_group.CreateSecurityGroup):
    def update_parser_network(self, parser):
        parser = super(CreateSecurityGroup, self).update_parser_network(parser)
        add_create_update_attributes(parser)
        return parser

    def take_action_network(self, client, parsed_args):
        # Build the create attributes.
        attrs = {}

        # Add Nuage attribute
        attrs.update(get_nuage_attrs(parsed_args))

        attrs['name'] = parsed_args.name
        attrs['description'] = self._get_description(parsed_args)
        if parsed_args.project is not None:
            identity_client = self.app.client_manager.identity
            project_id = security_group.identity_common.find_project(
                identity_client,
                parsed_args.project,
                parsed_args.project_domain,
            ).id
            attrs['tenant_id'] = project_id

        # Create the security group and display the results.
        obj = client.create_security_group(**attrs)
        display_columns, property_columns = _get_columns(obj)
        data = security_group.utils.get_item_properties(
            obj,
            property_columns,
            formatters=security_group._formatters_network
        )
        return display_columns, data


class ShowSecurityGroup(security_group.ShowSecurityGroup):
    pass


class SetSecurityGroup(security_group.SetSecurityGroup):
    def update_parser_network(self, parser):
        parser = super(SetSecurityGroup, self).update_parser_network(parser)
        add_create_update_attributes(parser)
        return parser

    def take_action_network(self, client, parsed_args):
        obj = client.find_security_group(parsed_args.group,
                                         ignore_missing=False)
        attrs = {}

        # Add Nuage attribute
        attrs.update(get_nuage_attrs(parsed_args))

        if parsed_args.name is not None:
            attrs['name'] = parsed_args.name
        if parsed_args.description is not None:
            attrs['description'] = parsed_args.description
        # NOTE(rtheis): Previous behavior did not raise a CommandError
        # if there were no updates. Maintain this behavior and issue
        # the update.
        client.update_security_group(obj, **attrs)
