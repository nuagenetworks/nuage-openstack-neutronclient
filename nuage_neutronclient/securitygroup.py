# Copyright 2018 NOKIA
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

from neutronclient.common import extension
from neutronclient.common import utils
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20
from neutronclient.neutron.v2_0 import securitygroup


class CreateSecurityGroup(extension.ClientExtensionCreate,
                          securitygroup.CreateSecurityGroup):
    shell_command = 'security-group-create'
    object_path = '/security-groups'

    def add_known_arguments(self, parser):
        super(CreateSecurityGroup, self).add_known_arguments(parser)
        utils.add_boolean_argument(
            parser, '--stateful',
            help=_('Defines whether the security group is stateful or not.'))

    def args2body(self, parsed_args):
        body = super(CreateSecurityGroup, self).args2body(parsed_args)
        if hasattr(parsed_args, 'stateful') and parsed_args.stateful:
            sec_group = body['security_group']
            sec_group['stateful'] = utils.str2bool(parsed_args.stateful)
        return body


class UpdateSecurityGroup(extension.ClientExtensionUpdate,
                          securitygroup.UpdateSecurityGroup):
    shell_command = 'security-group-update'
    resource_path = '/security-groups/%s'

    def add_known_arguments(self, parser):
        super(UpdateSecurityGroup, self).add_known_arguments(parser)
        utils.add_boolean_argument(
            parser, '--stateful',
            help=_('Defines whether the security group is stateful or not.'))

    def args2body(self, parsed_args):
        body = super(UpdateSecurityGroup, self).args2body(parsed_args)
        neutron_client = self.get_client()
        parsed_args.id = neutronV20.find_resourceid_by_name_or_id(
            neutron_client, self.resource, parsed_args.id)
        if hasattr(parsed_args, 'stateful') and parsed_args.stateful:
            sec_group = body['security_group']
            sec_group['stateful'] = utils.str2bool(parsed_args.stateful)
        return body
