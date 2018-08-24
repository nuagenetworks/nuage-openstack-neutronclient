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


class RedirectTarget(extension.NeutronClientExtension):
    resource = 'nuage_redirect_target'
    resource_plural = '%ss' % resource
    object_path = '/%ss' % resource.replace('_', '-')
    resource_path = '/%ss/%%s' % resource.replace('_', '-')
    versions = ['2.0']


class ListRedirectTarget(extension.ClientExtensionList, RedirectTarget):
    """List redirect targets that belong to a given subnet"""
    shell_command = 'nuage-redirect-target-list'
    list_columns = ['id', 'name', 'description', 'redundancy_enabled',
                    'insertion_mode']

    def get_parser(self, prog_name):
        parser = super(ListRedirectTarget, self).get_parser(prog_name)
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
        resp = super(ListRedirectTarget, self).take_action(parsed_args)
        return resp


class ShowRedirectTarget(extension.ClientExtensionShow, RedirectTarget):
    """Show information of a given redirect target."""

    shell_command = 'nuage-redirect-target-show'
    allow_names = True


class CreateRedirectTarget(extension.ClientExtensionCreate, RedirectTarget):
    """Create a redirect target for a given tenant."""

    shell_command = 'nuage-redirect-target-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'name', metavar='name',
            help='Name of redirect target to create.')
        parser.add_argument(
            '--insertion-mode',
            dest='insertion_mode',
            metavar='insertion_mode',
            choices=['L3', 'VIRTUAL_WIRE'],
            help='Insertion mode for redirection target')
        parser.add_argument(
            '--description', metavar='description',
            help='Description of redirect target.')
        parser.add_argument(
            '--redundancy-enabled',
            dest='redundancy_enabled', metavar='redundancy_enabled',
            help='Enable/Disable redundance on redirect target.')
        parser.add_argument(
            '--subnet', metavar='SUBNET',
            help='Subnet name or ID to add redirection target.')
        parser.add_argument(
            '--router', metavar='ROUTER',
            help='Router name or ID to add redirection target.')

    def args2body(self, parsed_args):
        body = {'nuage_redirect_target': {
            'name': parsed_args.name}}
        if not parsed_args.insertion_mode:
            message = (_('--insertion_mode should be specified'))
            raise exceptions.NeutronClientException(message=message)
        if not parsed_args.subnet and not parsed_args.router:
            message = (_('--subnet or --router should be specified'))
            raise exceptions.NeutronClientException(message=message)
        if parsed_args.description:
            body['nuage_redirect_target'].update(
                {'description': parsed_args.description})
        if parsed_args.redundancy_enabled:
            body['nuage_redirect_target'].update(
                {'redundancy_enabled': parsed_args.redundancy_enabled})
        if parsed_args.insertion_mode:
            body['nuage_redirect_target'].update(
                {'insertion_mode': parsed_args.insertion_mode})
        if parsed_args.subnet:
            _subnet_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'subnet', parsed_args.subnet)
            body['nuage_redirect_target'].update(
                {'subnet_id': _subnet_id})
        if parsed_args.router:
            _router_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'router', parsed_args.router)
            body['nuage_redirect_target'].update(
                {'router_id': _router_id})
        return body


class DeleteRedirectTarget(extension.ClientExtensionDelete, RedirectTarget):
    """Delete a given redirecttarget."""

    shell_command = 'nuage-redirect-target-delete'


class RedirectTargetVip(extension.NeutronClientExtension):
    resource = 'nuage_redirect_target_vip'
    resource_plural = '%ss' % resource
    object_path = '/%ss' % resource.replace('_', '-')
    resource_path = '/%ss/%%s' % resource.replace('_', '-')
    versions = ['2.0']


class CreateRedirectTargetVip(extension.ClientExtensionCreate,
                              RedirectTargetVip):
    """Create a redirect target for a given tenant."""

    shell_command = 'nuage-redirect-target-vip-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'subnet', metavar='SUBNET',
            help='Subnet name or ID to add redirection target.')
        parser.add_argument(
            'virtual_ip_address', metavar='VIRTUALIPADDRESS',
            help='Virtual IP Address.')
        parser.add_argument(
            'redirecttarget', metavar='REDIRECTTARGET',
            help=('ID or name of redirecttarget to add vip to.'))

    def args2body(self, parsed_args):
        body = {
            'nuage_redirect_target_vip': {
                'virtual_ip_address': parsed_args.virtual_ip_address,
            }
        }
        _subnet_id = neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'subnet', parsed_args.subnet)
        body['nuage_redirect_target_vip'].update(
            {'subnet_id': _subnet_id})
        _redirect_target_id = neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'nuage_redirect_target',
            parsed_args.redirecttarget)
        body['nuage_redirect_target_vip'].update(
            {'redirect_target_id': _redirect_target_id})
        return body


class RedirectTargetRule(extension.NeutronClientExtension):
    resource = 'nuage_redirect_target_rule'
    resource_plural = '%ss' % resource
    object_path = '/%ss' % resource.replace('_', '-')
    resource_path = '/%ss/%%s' % resource.replace('_', '-')
    versions = ['2.0']


class ListRedirectTargetRule(extension.ClientExtensionList,
                             RedirectTargetRule):
    """List redirect target rules that belong to a given tenant."""

    shell_command = 'nuage-redirect-target-rule-list'
    list_columns = ['id', 'action', 'protocol', 'priority', 'origin_group_id',
                    'port_range_min', 'port_range_max', 'remote_ip_prefix',
                    'remote_group_id', 'redirect_target_id']
    # replace_rules: key is an attribute name in Neutron API and
    # corresponding value is a display name shown by CLI.
    replace_rules = {'origin_group_id': 'origin_security_group',
                     'remote_group_id': 'remote_group'}

    def get_parser(self, prog_name):
        parser = super(ListRedirectTargetRule, self).get_parser(prog_name)
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
        if parsed_args.subnet:
            subnet = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'subnet', parsed_args.subnet)
        if parsed_args.router:
            router = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'router', parsed_args.router)
        if not parsed_args.subnet and not parsed_args.router:
            message = (_('--subnet or --router option should be specified'))
            raise exceptions.NeutronClientException(message=message)
        if subnet:
            self.values_specs.append('--subnet=%s' % subnet)
        if router:
            self.values_specs.append('--router=%s' % router)
        resp = super(ListRedirectTargetRule, self).take_action(parsed_args)
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
        info = super(ListRedirectTargetRule,
                     self).setup_columns(info, parsed_args)
        cols = info[0]
        cols = self.replace_columns(info[0], self.replace_rules)
        parsed_args.columns = cols
        return (cols, info[1])


class ShowRedirectTargetRule(extension.ClientExtensionShow,
                             RedirectTargetRule):
    """Show information of a given redirect target rule."""

    shell_command = 'nuage-redirect-target-rule-show'
    allow_names = False


class CreateRedirectTargetRule(extension.ClientExtensionCreate,
                               RedirectTargetRule):
    """Create a redirect target rule."""

    shell_command = 'nuage-redirect-target-rule-create'

    def add_known_arguments(self, parser):
        parser.add_argument(
            'redirect_target_id', metavar='REDIRECT_TARGET',
            help=_('Redirect Target ID to apply rule'))
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
            '--remote-ip-prefix',
            help=_('CIDR to match on.'))
        parser.add_argument(
            '--remote-group-id', metavar='REMOTE_GROUP',
            help=_('Remote security group name or ID to apply rule.'))
        parser.add_argument(
            '--origin-group-id', metavar='ORIGIN_SECURITY_GROUP',
            help=_('Origin security group name or ID to apply rule.'))
        parser.add_argument(
            '--priority',
            help=_('Priority of the rule that determines the order of'
                   ' the rule.'))
        parser.add_argument(
            '--action',
            help=_('The action of the rule FORWARD or REDIRECT.'))

    def args2body(self, parsed_args):
        _redirect_target_id = neutronV20.find_resourceid_by_name_or_id(
            self.get_client(), 'nuage_redirect_target',
            parsed_args.redirect_target_id)
        if parsed_args.origin_group_id:
            _origin_group_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'security_group',
                parsed_args.origin_group_id)
        else:
            message = (_('--origin-group-id should be specified'))
            raise exceptions.NeutronClientException(message=message)
        if parsed_args.action:
            _action = parsed_args.action
            if _action not in ['FORWARD', 'REDIRECT']:
                message = (_('valid rule action values are'
                             ' FORWARD or REDIRECT'))
                raise exceptions.NeutronClientException(message=message)
        else:
            message = (_('--action should be specified'))
            raise exceptions.NeutronClientException(message=message)

        body = {'nuage_redirect_target_rule': {
            'redirect_target_id': _redirect_target_id,
            'origin_group_id': _origin_group_id,
            'action': _action}}
        if parsed_args.priority:
            body['nuage_redirect_target_rule'].update(
                {'priority': parsed_args.priority})
        if parsed_args.protocol:
            body['nuage_redirect_target_rule'].update(
                {'protocol': parsed_args.protocol})
        if parsed_args.port_range_min:
            body['nuage_redirect_target_rule'].update(
                {'port_range_min': parsed_args.port_range_min})
        if parsed_args.port_range_max:
            body['nuage_redirect_target_rule'].update(
                {'port_range_max': parsed_args.port_range_max})
        if parsed_args.remote_ip_prefix:
            body['nuage_redirect_target_rule'].update(
                {'remote_ip_prefix': parsed_args.remote_ip_prefix})
        if parsed_args.remote_group_id:
            _remote_group_id = neutronV20.find_resourceid_by_name_or_id(
                self.get_client(), 'security_group',
                parsed_args.remote_group_id)
            body['nuage_redirect_target_rule'].update(
                {'remote_group_id': _remote_group_id})
        if parsed_args.remote_group_id and parsed_args.remote_ip_prefix:
            message = (_('Only remote_ip_prefix or remote_group_id may '
                         'be provided.'))
            raise exceptions.NeutronClientException(message=message)
        if parsed_args.tenant_id:
            body['nuage_redirect_target_rule'].update(
                {'tenant_id': parsed_args.tenant_id})

        return body


class DeleteRedirectTargetRule(extension.ClientExtensionDelete,
                               RedirectTargetRule):
    """Delete a given redirect target rule."""

    shell_command = 'nuage-redirect-target-rule-delete'
    allow_names = False
