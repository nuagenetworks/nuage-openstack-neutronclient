# Copyright 2015 Alcatel-Lucent USA Inc.
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
from neutronclient.i18n import _
from neutronclient.neutron import v2_0 as neutronV20


class UpdateFloatingIP(extension.ClientExtensionUpdate):
    resource = 'floatingip'
    shell_command = '%s-update' % resource
    resource_path = '/floatingips/%s'

    def add_known_arguments(self, parser):
        parser.add_argument(
            '--port-id',
            help=_('ID of the port to be associated with the floating IP.'))
        parser.add_argument(
            '--fixed-ip-address',
            help=_('IP address on the port (only required if port has '
                   'multiple IPs).'))
        parser.add_argument(
            '--nuage-fip-rate',
            help=_('Rate limiting applied to the floating IP. '
                   'Can be -1 for unlimited.'))

    def args2body(self, parsed_args):
        body = {self.resource: {}}
        updateables = ['port_id', 'fixed_ip_address', 'nuage_fip_rate']
        neutronV20.update_dict(parsed_args, body[self.resource], updateables)
        return body
