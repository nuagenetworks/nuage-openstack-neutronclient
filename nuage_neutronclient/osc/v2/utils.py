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

"""This module is intended to contain methods specific
to Networking v2 API and its extensions.
"""

from cliff import columns as cliff_columns
from osc_lib.utils import format_dict


class AdminStateColumn(cliff_columns.FormattableColumn):
    def human_readable(self):
        return 'UP' if self._value else 'DOWN'


def update_dict(obj, dict, attributes):
    """Update dict with fields from obj.attributes.

    :param obj: the object updated into dict
    :param dict: the result dictionary
    :param attributes: a list of attributes belonging to obj
    """
    for attribute in attributes:
        if hasattr(obj, attribute) and getattr(obj, attribute) is not None:
            dict[attribute] = getattr(obj, attribute)


def format_list_of_dicts(data):
    """Return a formatted string of key value pairs for each dict

    This method was copied from osc_lib and modified in order to sort its list
    :param data: a list of dicts
    :rtype: a string formatted to key='value' with dicts separated by new line
    """
    if data is None:
        return None

    return '\n'.join(sorted(format_dict(i) for i in data))
