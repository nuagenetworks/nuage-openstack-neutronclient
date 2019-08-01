# Copyright 2018 NOKIA
# All Rights Reserved
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

from neutronclient.v2_0 import client


class Client(client.ClientBase):

    nuage_l2bridge_path = "/nuage_l2bridges/{id}"
    nuage_l2bridges_path = "/nuage_l2bridges"
    nuage_policy_groups_path = "/nuage_policy_groups"
    nuage_floatingip_path = "/nuage_floatingips/{id}"
    nuage_floatingips_path = "/nuage_floatingips"
    nuage_redirect_targets_path = "/nuage_redirect_targets"
    nuage_vsd_resource = "/vsd_domains"
    nuage_netpartition_path = "/net_partitions/{id}"
    nuage_netpartitions_path = "/net_partitions"
    nuage_switchport_mappings_path = "/net-topology/switchport_mappings"
    nuage_switchport_mapping_path = "/net-topology/switchport_mappings/{id}"
    nuage_switchport_bindings_path = "/net-topology/switchport_bindings"
    nuage_switchport_binding_path = "/net-topology/switchport_bindings/{id}"

    # API has no way to report plurals, so we have to hard code them
    EXTED_PLURALS = {'nuage_l2bridges': 'nuage_l2bridge',
                     'nuage_policy_groups': 'nuage_policy_group',
                     'nuage_floating_ips': 'nuage_floating_ip',
                     'nuage_redirect_targets': 'nuage_redirect_target',
                     'vsd_domains': 'vsd_domain'}

    def __init__(self, **kwargs):
        """Initialize a new client via the Neutron v2.0 API."""
        super(Client, self).__init__(**kwargs)

    def _update_resource(self, path, **kwargs):
        revision_number = kwargs.pop('revision_number', None)
        if revision_number:
            headers = kwargs.setdefault('headers', {})
            headers['If-Match'] = 'revision_number={}'.format(revision_number)
        return self.put(path, **kwargs)

    def show_nuage_l2bridge(self, l2bridge, **_params):
        return self.get(self.nuage_l2bridge_path.format(id=l2bridge),
                        params=_params)

    def list_nuage_l2bridges(self, **_params):
        return self.get(self.nuage_l2bridges_path, params=_params)

    def create_nuage_l2bridge(self, body):
        return self.post(self.nuage_l2bridges_path, body=body)

    def update_nuage_l2bridge(self, l2bridge, body=None, revision_number=None):
        return self._update_resource(
            self.nuage_l2bridge_path.format(id=l2bridge),
            body=body, revision_number=revision_number)

    def delete_nuage_l2bridge(self, l2bridge_id):
        return self.delete(self.nuage_l2bridge_path.format(id=l2bridge_id))

    def create_switchport_mapping(self, body):
        return self.post(self.nuage_switchport_mappings_path, body=body)

    def delete_switchport_mapping(self, switchport_mapping_id):
        return self.delete(
            self.nuage_switchport_mapping_path.format(
                id=switchport_mapping_id))

    def list_switchport_mappings(self, **_params):
        return self.get(self.nuage_switchport_mappings_path, params=_params)

    def show_switchport_mapping(self, id, **_params):
        return self.get(self.nuage_switchport_mapping_path.format(id=id),
                        params=_params)

    def list_switchport_bindings(self, **_params):
        return self.get(self.nuage_switchport_bindings_path, params=_params)

    def show_switchport_binding(self, id, **_params):
        return self.get(self.nuage_switchport_binding_path.format(id=id),
                        params=_params)

    def update_switchport_mapping(self, switchport_id, body=None,
                                  revision_number=None):
        return self._update_resource(
            self.nuage_switchport_mapping_path.format(id=switchport_id),
            body=body, revision_number=revision_number)

    def create_net_partition(self, name):
        net_partition = {'net_partition': {'name': name}}
        return self.post(self.nuage_netpartitions_path, body=net_partition)

    def find_net_partition(self, name_or_id):
        return self.find_resource(resource='net_partition',
                                  name_or_id=name_or_id)

    def show_net_partition(self, id):
        return self.get(self.nuage_netpartition_path.format(id=id))

    def delete_net_partition(self, id):
        return self.delete(self.nuage_netpartition_path.format(id=id))

    def list_net_partitions(self, **params):
        return self.get(self.nuage_netpartitions_path, params=params)

    def list_nuage_policy_groups(self, **_params):
        return self.get(self.nuage_policy_groups_path, params=_params)

    def list_nuage_floatingips(self, **_params):
        return self.get(self.nuage_floatingips_path, params=_params)

    def show_nuage_floatingip(self, id, **_params):
        return self.get(self.nuage_floatingip_path.format(id=id),
                        params=_params)

    def list_nuage_redirect_targets(self, **_params):
        return self.get(self.nuage_redirect_targets_path, params=_params)

    def get_l3domain(self, router_id):
        domains = self.get(self.nuage_vsd_resource,
                           params={'os_router_ids': [router_id]})
        try:
            return domains['vsd_domains'][0]
        except Exception:
            return None
