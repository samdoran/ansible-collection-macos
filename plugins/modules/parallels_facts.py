#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
---
module: parallels_facts
author:
    - Sam Doran (@samdoran)
version_added: '2.11'
short_description: Gather information about Parallels using the C(prlsrvctl) command
notes: []
description:
    - Gather information about Parallels using the C(prlsrvctl) command.
options:
    opt1:
        description: []
"""

EXAMPLES = """
- name: Gather Parallels facts
  parallels_facts:
"""

RETURN = """
ansible_facts:
  description: Facts to add to ansible_facts
    returned: always
    type: complex
    contains:
      parallels:
        description:
          - Stuff
"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.process import get_bin_path


def main():
    module = AnsibleModule(
        argument_spec={},
        supports_check_mode=True,
    )

    prlsrvctl_bin = None
    try:
        prlsrvctl_bin = get_bin_path('prlsrvctl', ['/usr/local/bin/'])
    except ValueError:
        pass

    results = {'ansible_facts': {}}
    parallels_data = {
        'Version': {
            'Edition': '',
            'Full': '',
            'Major': '',
            'MajorMinor': '',
            'Release': '',
        }
    }
    if prlsrvctl_bin is not None:
        command = [prlsrvctl_bin, 'info', '--json']
        rc, out, err = module.run_command(command)
        if rc != 0:
            module.warn('Failed to gather Parallels facts')

        else:
            parallels_data = json.loads(out)

            # 'Version': 'Desktop 16.0.0-48916',
            version_string = parallels_data['Version']
            edition, full_version = version_string.split(' ', 1)
            parallels_data['Version'] = {}
            parallels_data['Version']['Edition'] = edition
            parallels_data['Version']['Full'] = full_version
            parallels_data['Version']['Major'] = full_version.split('.')[0]
            parallels_data['Version']['MajorMinor'] = full_version.split('-')[0]
            parallels_data['Version']['Release'] = full_version.split('-')[1]

    results['ansible_facts']['parallels'] = parallels_data

    module.exit_json(**results)


if __name__ == '__main__':
    main()
