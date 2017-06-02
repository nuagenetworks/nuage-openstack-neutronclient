# Copyright 2015 Alcatel-Lucent USA Inc.
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
#
from __future__ import print_function

from neutronclient.common import exceptions
from neutronclient.common import extension
from neutronclient.neutron import v2_0 as neutronV20

from nuage_neutronclient._i18n import _


class ExternalSecurityGroup(extension.NeutronClientExtension):
    resource = 'nuage_external_security_group'
    resource_plural = '%ss' % resource
    object_path = '/%ss' % resource.replace('_', '-')
    resource_path = '/%ss/%%s' % resource.replace('_', '-')
    versions = ['2.0']


class ListExternalSecurityGroup(extension.ClientExtensionList,
                                ExternalSecurityGroup):
    """List External Security Groups that belong to a given subnet"""
    shell_command = 'nuage-external-security-group-list'
    list_columns = ['id', 'name', 'description', 'extended_community_id']

    def get_parser(self, prog_name):
        parser = super(ListExternalSecurityGroup, self).get_parser(prog_name)
        parser.add_argument(
            '--subnet', metavar='subnet',
            help=('ID or name of subnet to look up.'))
        parser.add_argument(
            '--router', metavar='router',
            help=('ID or name of router to look up.'))
        return parser

    def take_action(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        subnet = None
        router = None
        if not parsed_args.subnet and not parsed_args.router:
            message = (_('--subnet or --router option should be specified'))
            raise exceptions.NeutronClientException(message=message)
        if parsed_args.subnet:
            subnet = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'subnet', parsed_args.subnet)
            self.values_specs.append('--subnet=%s' % subnet)
        if parsed_args.router:
            router = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'router', parsed_args.router)
            self.values_specs.append('--router=%s' % router)
        resp = super(ListExternalSecurityGroup, self).take_action(parsed_args)
        return resp


class ShowExternalSecurityGroup(extension.ClientExtensionShow,
                                ExternalSecurityGroup):
    """Show information of a given External Security Group."""

    shell_command = 'nuage-external-security-group-show'
    allow_names = True


class CreateExternalSecurityGroup(extension.ClientExtensionCreate,
                                  ExternalSecurityGroup):
    """Create a External Security Group for a given tenant."""

    shell_command = 'nuage-external-security-group-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'extended_community',
            metavar='extended_community',
            help='An extended community or other similar BGP attribute.')
        parser.add_argument(
            'name', metavar='name',
            help='Name of external security group to create.')
        parser.add_argument(
            '--description', metavar='description',
            help='Description of redirect target.')
        parser.add_argument(
            '--subnet', metavar='SUBNET',
            help='Subnet name or ID to add redirection target.')
        parser.add_argument(
            '--router', metavar='ROUTER',
            help='Router name or ID to add redirection target.')

    def args2body(self, parsed_args):
        body = {'nuage_external_security_group': {
            'name': parsed_args.name,
            'extended_community_id': parsed_args.extended_community}}
        if not parsed_args.subnet and not parsed_args.router:
            message = (_('--subnet or --router should be specified'))
            raise exceptions.NeutronClientException(message=message)
        if parsed_args.description:
            body['nuage_external_security_group'].update(
                {'description': parsed_args.description})
        if parsed_args.subnet:
            _subnet_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'subnet', parsed_args.subnet)
            body['nuage_external_security_group'].update(
                {'subnet_id': _subnet_id})
        if parsed_args.router:
            _router_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'router', parsed_args.router)
            body['nuage_external_security_group'].update(
                {'router_id': _router_id})
        return body


class DeleteExternalSecurityGroup(extension.ClientExtensionDelete,
                                  ExternalSecurityGroup):
    """Delete a given External Security Group."""

    shell_command = 'nuage-external-security-group-delete'


class ExternalSecurityGroupRule(extension.NeutronClientExtension):
    resource = 'nuage_external_security_group_rule'
    resource_plural = '%ss' % resource
    object_path = '/%ss' % resource.replace('_', '-')
    resource_path = '/%ss/%%s' % resource.replace('_', '-')
    versions = ['2.0']


class ListExternalSecurityGroupRule(extension.ClientExtensionList,
                                    ExternalSecurityGroupRule):
    """List external security group rules that belong to a given tenant."""

    shell_command = 'nuage-external-security-group-rule-list'
    list_columns = ['id', 'protocol', 'direction', 'origin_group_id',
                    'port_range_min', 'port_range_max',
                    'remote_external_group_id']
    # replace_rules: key is an attribute name in Neutron API and
    # corresponding value is a display name shown by CLI.
    replace_rules = {'origin_group_id': 'origin_security_group',
                     'remote_external_group_id': 'remote_group'}

    def get_parser(self, prog_name):
        parser = super(ListExternalSecurityGroupRule,
                       self).get_parser(prog_name)
        parser.add_argument(
            'remote_external_group', metavar='REMOTE_GROUP',
            help=('ID or name of external security group to look up.'))
        return parser

    def take_action(self, parsed_args):
        neutron_client = self.get_client()
        neutron_client.format = parsed_args.request_format
        _external_group_id = neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'nuage_external_security_group',
            parsed_args.remote_external_group)
        self.values_specs.append('--external_group=%s' % _external_group_id)
        resp = super(ListExternalSecurityGroupRule, self).take_action(
            parsed_args)
        return resp

    @staticmethod
    def replace_columns(cols, rules, reverse=False):
        if reverse:
            rules = dict((rules[k], k) for k in rules.keys())
        return [rules.get(col, col) for col in cols]

    def _get_sg_name_dict(self, data):
        """Get names of security groups referred in the retrieved rules.

        :return: a dict from secgroup ID to secgroup name
        """
        neutron_client = self.get_client()
        search_opts = {'fields': ['id', 'name']}
        sec_group_ids = set()
        for rule in data:
            for key in self.replace_rules:
                if rule.get(key):
                    sec_group_ids.add(rule[key])
        sec_group_ids = list(sec_group_ids)

        def _get_sec_group_list(sec_group_ids):
            search_opts['id'] = sec_group_ids
            resp = neutron_client.list_security_groups(
                **search_opts).get('security_groups', [])
            return resp

        try:
            secgroups = _get_sec_group_list(sec_group_ids)
        except exceptions.RequestURITooLong as uri_len_exc:
            # Length of a query filter on security group rule id
            # id=<uuid>& (with len(uuid)=36)
            sec_group_id_filter_len = 40
            # The URI is too long because of too many sec_group_id filters
            # Use the excess attribute of the exception to know how many
            # sec_group_id filters can be inserted into a single request
            sec_group_count = len(sec_group_ids)
            max_size = ((sec_group_id_filter_len * sec_group_count) -
                        uri_len_exc.excess)
            chunk_size = max_size // sec_group_id_filter_len
            secgroups = []
            for i in range(0, sec_group_count, chunk_size):
                secgroups.extend(
                    _get_sec_group_list(sec_group_ids[i: i + chunk_size]))

        return dict([(sg['id'], sg['name'])
                     for sg in secgroups if sg['name']])

    @staticmethod
    def _has_fileds(rule, required_fileds):
        return all([key in rule for key in required_fileds])

    def extend_list(self, data, parsed_args):
        sg_dict = self._get_sg_name_dict(data)
        for rule in data:
            # Replace security group UUID with its name.
            for key in self.replace_rules:
                if key in rule:
                    rule[key] = sg_dict.get(rule[key], rule[key])

    def setup_columns(self, info, parsed_args):
        # Translate the specified columns from the command line
        # into field names used in "info".
        parsed_args.columns = self.replace_columns(parsed_args.columns,
                                                   self.replace_rules,
                                                   reverse=True)
        info = super(ListExternalSecurityGroupRule,
                     self).setup_columns(info, parsed_args)
        cols = info[0]
        cols = self.replace_columns(info[0], self.replace_rules)
        parsed_args.columns = cols
        return (cols, info[1])


class ShowExternalSecurityGroupRule(extension.ClientExtensionShow,
                                    ExternalSecurityGroupRule):
    """Show information of a given external security group rule."""

    shell_command = 'nuage-external-security-group-rule-show'
    allow_names = False


class CreateExternalSecurityGroupRule(extension.ClientExtensionCreate,
                                      ExternalSecurityGroupRule):
    """Create a external security group rule."""

    shell_command = 'nuage-external-security-group-rule-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--direction',
            default='ingress', choices=['ingress', 'egress'],
            help=_('Direction of traffic: ingress/egress.'))
        parser.add_argument(
            '--protocol',
            help=_('Protocol of packet.'))
        parser.add_argument(
            '--port-range-min',
            help=_('Starting port range.'))
        parser.add_argument(
            '--port-range-max',
            help=_('Ending port range.'))
        parser.add_argument(
            'remote_external_group_id', metavar='REMOTE_GROUP',
            help=_('Remote exteranl security group name or ID to apply rule.'))
        parser.add_argument(
            '--origin-group-id', metavar='ORIGIN_SECURITY_GROUP',
            help=_('Origin security group name or ID to apply rule.'))

    def args2body(self, parsed_args):
        _external_group_id = neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'nuage_external_security_group',
            parsed_args.remote_external_group_id)
        if parsed_args.origin_group_id:
            _origin_group_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'security_group',
                parsed_args.origin_group_id)
        else:
            message = (_('--origin-group-id should be specified'))
            raise exceptions.NeutronClientException(message=message)

        body = {'nuage_external_security_group_rule': {
            'direction': parsed_args.direction,
            'remote_external_group_id': _external_group_id,
            'origin_group_id': _origin_group_id}}
        if parsed_args.protocol:
            body['nuage_external_security_group_rule'].update(
                {'protocol': parsed_args.protocol})
        if parsed_args.port_range_min:
            body['nuage_external_security_group_rule'].update(
                {'port_range_min': parsed_args.port_range_min})
        if parsed_args.port_range_max:
            body['nuage_external_security_group_rule'].update(
                {'port_range_max': parsed_args.port_range_max})
        if parsed_args.tenant_id:
            body['nuage_redirect_target_rule'].update(
                {'tenant_id': parsed_args.tenant_id})

        return body


class DeleteExternalSecurityGroupRule(extension.ClientExtensionDelete,
                                      ExternalSecurityGroupRule):
    """Delete a given external security group rule."""

    shell_command = 'nuage-external-security-group-rule-delete'
    allow_names = False
