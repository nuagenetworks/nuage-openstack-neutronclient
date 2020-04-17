#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

"""Network segment action implementations"""

from openstackclient.network.v2 import network_segment


class CreateNetworkSegment(network_segment.CreateNetworkSegment):

    def get_parser(self, prog_name):
        parser = super(CreateNetworkSegment, self).get_parser(prog_name)
        for action in parser._optionals._actions:
            if action.dest == 'network_type':
                action.choices = ['flat', 'geneve', 'gre', 'local', 'vlan',
                                  'vxlan', 'nuage_hybrid_mpls']
                action.help = ('Network type of this network segment '
                               '(flat, geneve, gre, local, vlan, vxlan or '
                               'nuage_hybrid_mpls)')
        return parser
