# Copyright 2016 Alcatel-Lucent USA Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from neutronclient.common import exceptions
from neutronclient.common import extension
from neutronclient.common.utils import is_valid_cidr
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20
from neutronclient.neutron.v2_0 import port
from nuage_neutronclient import nuage_floatingip
from nuage_neutronclient import nuage_policy_group


def _add_known_arguments(parser):
    parser.add_argument(
        '--nuage-floatingip',
        help=_('ID or IP of the floatingip on VSD to link with this port.'))
    parser.add_argument(
        '--nuage-policy-groups', action='append',
        help=_('IDs or names of the policy groups to attach to this port.'))
    parser.add_argument(
        '--nuage-redirect-targets',
        help=_('ID(s) or name(s) of the redirect target(s)'
               ' to assign to this port.'))


def _args2body(port, parsed_args):
    if parsed_args.nuage_floatingip:
        port['nuage_floatingip'] = {'id': parsed_args.nuage_floatingip}
    if parsed_args.nuage_policy_groups:
        port['nuage_policy_groups'] = parsed_args.nuage_policy_groups
    if parsed_args.nuage_redirect_targets:
        port['nuage_redirect_targets'] = parsed_args.nuage_redirect_targets


def handle_pg_names(neutron_client, parsed_args, during_create=False):
    policy_groups = parsed_args.nuage_policy_groups
    pg_ids = []
    for pg in policy_groups:
        if during_create:
            policy_groups = neutron_client.list_nuage_policy_groups(
                name=pg)[nuage_policy_group.NuagePolicyGroup.resource_plural]
        else:
            policy_groups = neutron_client.list_nuage_policy_groups(
                for_port=parsed_args.id,
                name=pg
            )[nuage_policy_group.NuagePolicyGroup.resource_plural]
        if len(policy_groups) == 1:
            pg_ids.append(policy_groups[0]['id'])
        elif len(policy_groups) > 1:
            msg = _("Multiple policy groups exist with name %s") % pg
            raise exceptions.NeutronClientException(message=msg,
                                                    status_code=400)
        else:
            pg_ids.append(pg)
    parsed_args.nuage_policy_groups = pg_ids


def handle_fip_ips(neutron_client, parsed_args):
    floatingips = neutron_client.list_nuage_floatingips(
        for_port=parsed_args.id,
        floating_ip_address=parsed_args.nuage_floatingip
    )[nuage_floatingip.NuageFloatingIp.resource_plural]
    if len(floatingips) == 1:
        parsed_args.nuage_floatingip = floatingips[0]['id']
    elif len(floatingips) > 1:
        msg = (_("Multiple floatingips exist with IP %s")
               % parsed_args.nuage_floatingip)
        raise exceptions.NeutronClientException(message=msg,
                                                status_code=400)
    else:
        msg = (_("No floatingip available with IP %(ip)s for port %(port)s")
               % {'ip': parsed_args.nuage_floatingip, 'port': parsed_args.id})
        raise exceptions.NeutronClientException(message=msg,
                                                status_code=404)


class CreatePort(extension.ClientExtensionCreate,
                 port.CreatePort):
    shell_command = 'port-create'
    object_path = '/ports'

    def add_known_arguments(self, parser):
        super(CreatePort, self).add_known_arguments(parser)
        _add_known_arguments(parser)

    def args2body(self, parsed_args):
        body = super(CreatePort, self).args2body(parsed_args)
        neutron_client = self.get_client()

        if is_valid_cidr(parsed_args.nuage_floatingip):
            handle_fip_ips(neutron_client, parsed_args)
        if parsed_args.nuage_policy_groups:
            handle_pg_names(neutron_client, parsed_args,
                            during_create=True)

        port = body['port']
        _args2body(port, parsed_args)
        return body


class UpdatePort(extension.ClientExtensionUpdate,
                 port.UpdatePort):
    shell_command = 'port-update'
    resource_path = '/ports/%s'

    def add_known_arguments(self, parser):
        super(UpdatePort, self).add_known_arguments(parser)
        parser.add_argument(
            '--no-nuage-floatingip',
            action='store_true',
            help=_('Disassociate the floating ip on VSD.'))
        parser.add_argument(
            '--no-nuage-policy-groups',
            action='store_true',
            help=_('Disassociate the policy groups on VSD.'))
        parser.add_argument(
            '--no-nuage-redirect-targets',
            action='store_true',
            help=_('Disassociate the redirect target on VSD.'))
        _add_known_arguments(parser)

    def args2body(self, parsed_args):
        body = super(UpdatePort, self).args2body(parsed_args)
        neutron_client = self.get_client()
        parsed_args.id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, self.resource, parsed_args.id)

        if is_valid_cidr(parsed_args.nuage_floatingip):
            handle_fip_ips(neutron_client, parsed_args)
        if parsed_args.nuage_policy_groups:
            handle_pg_names(neutron_client, parsed_args)

        port = body['port']
        _args2body(port, parsed_args)
        if parsed_args.no_nuage_floatingip:
            port['nuage_floatingip'] = None
        if parsed_args.no_nuage_policy_groups:
            port['nuage_policy_groups'] = []
        if parsed_args.no_nuage_redirect_targets:
            port['nuage_redirect_targets'] = []
        return body
