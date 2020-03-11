# Copyright 2018 OPENSTACK
# Copyright 2018 NOKIA
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
import copy
import re

from neutronclient.common import exceptions as neutron_exceptions
from neutronclient.v2_0.client import UUID_PATTERN
from openstack.network.v2.port import Port as port_resource
from openstack import resource
from openstackclient.network import common as network_common
from openstackclient.network.v2 import port
from osc_lib import exceptions
from osc_lib import utils as osc_utils
from osc_lib.utils import tags as _tag
from oslo_utils import netutils

from nuage_neutronclient._i18n import _


# Add Nuage specific attributes to Openstack port
port_resource.nuage_floatingip = resource.Body('nuage_floatingip')
port_resource.nuage_policy_groups = resource.Body('nuage_policy_groups',
                                                  type=list)
port_resource.nuage_redirect_targets = resource.Body('nuage_redirect_targets')

# Formatters for Nuage specific attributes
port._formatters.update({'nuage_floatingip': osc_utils.format_dict,
                         'nuage_policy_groups': osc_utils.format_list,
                        # for historic reasons, rtarget is a list in plugin api
                         'nuage_redirect_targets': osc_utils.format_list})

super_get_attrs = port._get_attrs


def add_arguments_for_set_create(parser):
    """Add arguments for port create and port set commands"""
    parser.add_argument(
        '--nuage-floatingip',
        metavar='<nuage-floatingip>',
        help=_('ID or IP of the floatingip on VSD to link with this port.'))
    parser.add_argument(
        '--nuage-policy-group',
        metavar='<nuage-policy-group>',
        action='append',
        help=_('Desired Nuage Policygroup for this port (Name or ID) '
               '(repeat option to set multiple Nuage policygroups)'))
    parser.add_argument(
        '--nuage-redirect-target',
        metavar='<nuage-redirect-target>',
        help=_('ID or IP of the redirect target on VSD to link with this '
               'port.'))


def convert_pg_names_to_ids(nuageclient, policy_group_name_or_ids):
    """Convert nuage policygroup name or ids to only ids"""
    return (nuageclient.find_resource('nuage_policy_group', name_or_id)['id']
            for name_or_id in policy_group_name_or_ids)


def convert_rt_name_to_id(nuageclient, redirect_target_name_or_id):
    """Convert nuage redirect target name or ids to only ids"""
    return nuageclient.find_resource('nuage_redirect_target',
                                     redirect_target_name_or_id)['id']


def get_nuage_floating_ip(nuageclient, nuage_floating_ip_parsed_arg):
    """Convert to Nuage floating ip id"""
    nuage_fip = nuage_floating_ip_parsed_arg
    if netutils.is_valid_ipv4(nuage_floating_ip_parsed_arg):
        floatingips = nuageclient.list_nuage_floatingips(
            floating_ip_address=nuage_floating_ip_parsed_arg
        )['nuage_floatingips']
        if len(floatingips) == 1:
            nuage_fip = floatingips[0]['id']
        elif len(floatingips) > 1:
            msg = _("Multiple Nuage Floating IP exist with IP {}").format(
                nuage_floating_ip_parsed_arg)
            raise exceptions.CommandError(msg)
        else:
            msg = _("No Nuage Floating IP available with IP {}").format(
                nuage_floating_ip_parsed_arg)
            raise exceptions.CommandError(msg)
    else:
        if not re.match(UUID_PATTERN, nuage_floating_ip_parsed_arg):
            raise exceptions.CommandError(
                _('"--nuage-floatingip" should be UUID '
                  'or valid IP, but is "{}".').format(
                    nuage_floating_ip_parsed_arg))
    return nuage_fip


def get_nuage_policygroups(nuageclient, port_id):
    """Get Nuage policygroups that are attached to a specific port"""
    return (pg['id'] for pg in nuageclient.list_nuage_policy_groups(
        ports=[port_id],
        fields=['id'])['nuage_policy_groups'])


def get_nuage_redirect_target(nuageclient, port_id):
    """Get Nuage redirect target that is attached to a specific port"""
    rt = nuageclient.list_nuage_redirect_targets(
        ports=[port_id],
        fields=['id'])['nuage_redirect_targets']
    return rt[0] if rt else None


def get_nuage_attrs_port_create(client_manager, parsed_args):
    attrs = super_get_attrs(client_manager, parsed_args)

    # Add Nuage Attributes
    nuageclient = client_manager.nuageclient

    if parsed_args.nuage_floatingip:

        fip_id = get_nuage_floating_ip(
            nuageclient, parsed_args.nuage_floatingip)
        if fip_id:
            attrs['nuage_floatingip'] = {'id': fip_id}

    if parsed_args.nuage_redirect_target:
        attrs['nuage_redirect_targets'] = convert_rt_name_to_id(
            nuageclient, parsed_args.nuage_redirect_target)

    if parsed_args.nuage_policy_group:
        attrs['nuage_policy_groups'] = list(convert_pg_names_to_ids(
            nuageclient, parsed_args.nuage_policy_group))

    return attrs


class ShowPort(port.ShowPort):

    def __init__(self, *args, **kwargs):
        super(ShowPort, self).__init__(*args, **kwargs)

    def _handle_nuage_specific_attributes(self, port):
        """Fetch extra Nuage attributes for the port that we have to show"""

        if not port:
            return

        nuageclient = self.app.client_manager.nuageclient

        try:
            # Fetch Nuage policy groups
            pgs = get_nuage_policygroups(nuageclient, port.id)
            port.nuage_policy_groups = list(pgs) or None

            # Fetch Nuage redirect target
            rt = get_nuage_redirect_target(nuageclient, port.id)
            port.nuage_redirect_targets = [rt['id']] if rt else None

            # Fetch Nuage floating ip
            fips = nuageclient.list_nuage_floatingips(
                ports=[port.id], fields=['id', 'floating_ip_address'])
            port.nuage_floatingip = (fips['nuage_floatingips'][0]
                                     if fips['nuage_floatingips'] else None)
        except neutron_exceptions.BadRequest:
            # TODO(glenn) Can we find better way to detect a port with no vport
            pass

    def take_action(self, parsed_args):
        client = self.app.client_manager.network
        obj = client.find_port(parsed_args.port, ignore_missing=False)

        self._handle_nuage_specific_attributes(obj)

        display_columns, columns = port._get_columns(obj)
        data = osc_utils.get_item_properties(obj, columns,
                                             formatters=port._formatters)
        return display_columns, data


class UnsetPort(port.UnsetPort):

    def get_parser(self, prog_name):
        parser = super(UnsetPort, self).get_parser(prog_name)
        parser.add_argument(
            '--nuage-floatingip',
            action='store_true',
            default=False,
            help=_('Remove the nuage floating IP attached to the port.'))
        parser.add_argument(
            '--nuage-redirect-target',
            action='store_true',
            help=_('Remove the nuage redirect target attached to the port.'))
        parser.add_argument(
            '--nuage-policy-group',
            metavar='<nuage-policy-group>',
            action='append',
            help=_(
                'Desired Nuage Policygroup (Name or ID) which should be '
                'removed from this port (repeat option to unset multiple '
                'Nuage Policygroups)'))

        return parser

    @staticmethod
    def _handle_nuage_specific_attributes(parsed_args, attrs, port,
                                          nuageclient):
        """Unset Nuage attributes for the port"""

        if not port:
            return  # No port found

        if parsed_args.nuage_floatingip:
            attrs['nuage_floatingip'] = None

        if parsed_args.nuage_redirect_target:
            attrs['nuage_redirect_targets'] = []

        if parsed_args.nuage_policy_group:
            # get current policygroups
            pg_ids = get_nuage_policygroups(nuageclient, port.id)

            # remove the passed policygroups from the list
            excluded_pg_ids = set(convert_pg_names_to_ids(
                nuageclient, parsed_args.nuage_policy_group))
            attrs['nuage_policy_groups'] = [
                pg_id for pg_id in pg_ids
                if pg_id not in excluded_pg_ids]

    def take_action(self, parsed_args):
        # Copied from overwritten method!

        client = self.app.client_manager.network
        obj = client.find_port(parsed_args.port, ignore_missing=False)
        # SDK ignores update() if it receives a modified obj and attrs
        # To handle the same tmp_obj is created in all take_action of
        # Unset* classes
        tmp_fixed_ips = copy.deepcopy(obj.fixed_ips)
        tmp_binding_profile = copy.deepcopy(obj.binding_profile)
        tmp_secgroups = copy.deepcopy(obj.security_group_ids)
        tmp_addr_pairs = copy.deepcopy(obj.allowed_address_pairs)
        port._prepare_fixed_ips(self.app.client_manager, parsed_args)
        attrs = {}
        if parsed_args.fixed_ip:
            try:
                for ip in parsed_args.fixed_ip:
                    tmp_fixed_ips.remove(ip)
            except ValueError:
                msg = _("Port does not contain fixed-ip %s") % ip
                raise exceptions.CommandError(msg)
            attrs['fixed_ips'] = tmp_fixed_ips
        if parsed_args.binding_profile:
            try:
                for key in parsed_args.binding_profile:
                    del tmp_binding_profile[key]
            except KeyError:
                msg = _("Port does not contain binding-profile %s") % key
                raise exceptions.CommandError(msg)
            attrs['binding:profile'] = tmp_binding_profile
        if parsed_args.security_group_ids:
            try:
                for sg in parsed_args.security_group_ids:
                    sg_id = client.find_security_group(
                        sg, ignore_missing=False).id
                    tmp_secgroups.remove(sg_id)
            except ValueError:
                msg = _("Port does not contain security group %s") % sg
                raise exceptions.CommandError(msg)
            attrs['security_group_ids'] = tmp_secgroups
        if parsed_args.allowed_address_pairs:
            try:
                for addr in port._convert_address_pairs(parsed_args):
                    tmp_addr_pairs.remove(addr)
            except ValueError:
                msg = _("Port does not contain allowed-address-pair %s") % addr
                raise exceptions.CommandError(msg)
            attrs['allowed_address_pairs'] = tmp_addr_pairs
        if parsed_args.qos_policy:
            attrs['qos_policy_id'] = None
        if parsed_args.data_plane_status:
            attrs['data_plane_status'] = None

        # Nuage specific attributes
        self._handle_nuage_specific_attributes(
            parsed_args, attrs, obj, self.app.client_manager.nuageclient)

        if attrs:
            client.update_port(obj, **attrs)

        # tags is a subresource and it needs to be updated separately.
        _tag.update_tags_for_unset(client, obj, parsed_args)


class SetPort(port.SetPort):

    def get_parser(self, prog_name):
        parser = super(SetPort, self).get_parser(prog_name)
        add_arguments_for_set_create(parser)

        parser.add_argument(
            '--no-nuage-policy-groups',
            action='store_true',
            help=_("Clear existing information of Nuage Policygroup."
                   "Specify both --nuage-policygroup and "
                   "--no-nuage-policygroup to overwrite the current Nuage "
                   "policygroups")
        )

        return parser

    @staticmethod
    def _handle_nuage_specific_attributes(parsed_args, attrs, port,
                                          nuageclient):
        """Set Nuage attributes for the port"""

        if not port:
            return  # no port found to set data on

        if parsed_args.nuage_floatingip:
            fip_id = get_nuage_floating_ip(
                nuageclient, parsed_args.nuage_floatingip)
            if fip_id:
                attrs['nuage_floatingip'] = {'id': fip_id}

        if parsed_args.nuage_redirect_target:
            rt_id = convert_rt_name_to_id(nuageclient,
                                          parsed_args.nuage_redirect_target)
            if rt_id:
                attrs['nuage_redirect_targets'] = [rt_id]

        if parsed_args.no_nuage_policy_groups:
            # overwrite the existing Nuage policygroups
            attrs['nuage_policy_groups'] = []
        elif parsed_args.nuage_policy_group:
            # start from the existing policygroups
            attrs['nuage_policy_groups'] = list(
                get_nuage_policygroups(nuageclient, port.id))

        if parsed_args.nuage_policy_group:
            # extend with the new policygroups
            new_pgs = convert_pg_names_to_ids(
                nuageclient, parsed_args.nuage_policy_group)
            attrs['nuage_policy_groups'].extend(new_pgs)

    def take_action(self, parsed_args):
        client = self.app.client_manager.network

        port._prepare_fixed_ips(self.app.client_manager, parsed_args)
        obj = client.find_port(parsed_args.port, ignore_missing=False)
        attrs = super_get_attrs(self.app.client_manager, parsed_args)

        if parsed_args.no_binding_profile:
            attrs['binding:profile'] = {}
        if parsed_args.binding_profile:
            if 'binding:profile' not in attrs:
                attrs['binding:profile'] = copy.deepcopy(obj.binding_profile)
            attrs['binding:profile'].update(parsed_args.binding_profile)

        if parsed_args.no_fixed_ip:
            attrs['fixed_ips'] = []
        if parsed_args.fixed_ip:
            if 'fixed_ips' not in attrs:
                # obj.fixed_ips = [{}] if no fixed IPs are set.
                # Only append this to attrs['fixed_ips'] if actual fixed
                # IPs are present to avoid adding an empty dict.
                attrs['fixed_ips'] = [ip for ip in obj.fixed_ips if ip]
            attrs['fixed_ips'].extend(parsed_args.fixed_ip)

        if parsed_args.no_security_group:
            attrs['security_group_ids'] = []
        if parsed_args.security_group:
            if 'security_group_ids' not in attrs:
                # NOTE(dtroyer): Get existing security groups, iterate the
                #                list to force a new list object to be
                #                created and make sure the SDK Resource
                #                marks the attribute 'dirty'.
                attrs['security_group_ids'] = [
                    id for id in obj.security_group_ids
                ]
            attrs['security_group_ids'].extend(
                client.find_security_group(sg, ignore_missing=False).id
                for sg in parsed_args.security_group
            )

        if parsed_args.no_allowed_address_pair:
            attrs['allowed_address_pairs'] = []
        if parsed_args.allowed_address_pairs:
            if 'allowed_address_pairs' not in attrs:
                attrs['allowed_address_pairs'] = (
                    [addr for addr in obj.allowed_address_pairs if addr]
                )
            attrs['allowed_address_pairs'].extend(
                port_resource._convert_address_pairs(parsed_args)
            )
        if parsed_args.data_plane_status:
            attrs['data_plane_status'] = parsed_args.data_plane_status

        # Nuage specific attributes
        self._handle_nuage_specific_attributes(
            parsed_args, attrs, obj, self.app.client_manager.nuageclient)

        if attrs:
            with network_common.check_missing_extension_if_error(
                    self.app.client_manager.network, attrs):
                client.update_port(obj, **attrs)

        # tags is a subresource and it needs to be updated separately.
        _tag.update_tags_for_set(client, obj, parsed_args)


port._get_attrs = get_nuage_attrs_port_create


class CreatePort(port.CreatePort):

    def get_parser(self, prog_name):
        parser = super(CreatePort, self).get_parser(prog_name)
        add_arguments_for_set_create(parser)
        return parser
