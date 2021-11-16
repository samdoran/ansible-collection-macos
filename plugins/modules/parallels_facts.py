#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = """
module: parallels_facts
author:
  - Sam Doran (@samdoran)
version_added: '1.0.0'
short_description: Gather information about Parallels using the C(prlsrvctl) command
notes: []
description:
  - Gather information about Parallels using the C(prlsrvctl) command.
"""

EXAMPLES = """
- name: Gather Parallels facts
  samdoran.macos.parallels_facts:
"""

RETURN = """
ansible_facts:
  description: Facts to add to ansible_facts
  returned: always
  type: dict
  contains:
    parallels:
      type: dict
      description: Data returned from C(prlsrvctl info). Not all values are documented.
      contains:
        Hardware info:
          description: Hardware devices
          type: list
          elements: dict
        Hostname:
          description: Parallels host name
          type: str
        ID:
          description: Parallels host ID
          type: str
        License:
          description: Parallels license information
          type: dict
          contains:
            key:
              description: License key
              type: str
              sample: A8GZ1H-******-******-******-7N2HQG
        OS:
          description: Operating system version
          type: str
          sample: Mac OS X 10.15.6(19G2021)
        VMs:
          description: List of VMs registered to Parallels
          type: list
          elements: dict
          sample:
            - name: windows-2016
              ip_configured: 10.111.77.22
              status: running
              uuid: c9eb5191-c85e-4758-bfe7-a983c79af343
            - name: macOS-10.15
              ip_configured: '-'
              status: stopped
              uuid: e711eb50-1c80-43ef-9f74-86f7a0a6f387
            - name: rhel-9
              ip_configured: 10.72.22.3
              status: running
              uuid: 39a76fba-275e-4d54-8227-281e1346641e
        Version:
          description: Parallels version information
          type: dict
          sample:
            Edition: Desktop
            Full: 16.0.0-48916
            Major: '16'
            MajorMinor: 16.0.0
            Release: '48916'

"""

import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils.common.text.converters import to_native

# command: python -c 'import prlsdkapi; prlsdkapi.init_desktop_sdk(); print(prlsdkapi.ApiHelper().get_version()); prlsdkapi.deinit_sdk()'

HAS_PARALLELS_SDK = True
try:
    import prlsdkapi
except ImportError:
    HAS_PARALLELS_SDK = False


def get_sdk_version():
    sdk_version = ''
    if HAS_PARALLELS_SDK:
        prlsdkapi.init_desktop_sdk()
        sdk_version = prlsdkapi.ApiHelper().get_version()
        prlsdkapi.deinit_sdk()

    return to_native(sdk_version)


def get_server_info(module, data):
    prlsrvctl_bin = None
    try:
        prlsrvctl_bin = get_bin_path('prlsrvctl', ['/usr/local/bin/'])
    except ValueError:
        pass

    if prlsrvctl_bin is not None:
        command = [prlsrvctl_bin, 'info', '--json']
        rc, out, err = module.run_command(command)
        if rc != 0:
            module.warn('Failed to gather Parallels facts')

        else:
            srv_info = json.loads(out)

            for k in srv_info:
                data[k] = srv_info[k]

            # 'Version': 'Desktop 16.0.0-48916',
            version_string = srv_info['Version']
            edition, full_version = version_string.split(' ', 1)
            data['Version'] = {}
            data['Version']['Edition'] = edition
            data['Version']['Full'] = full_version
            data['Version']['Major'] = full_version.split('.')[0]
            data['Version']['MajorMinor'] = full_version.split('-')[0]
            data['Version']['Release'] = full_version.split('-')[1]


def get_vm_info(module, data):
    prlctl_bin = None
    try:
        prlctl_bin = get_bin_path('prlctl', ['/usr/local/bin'])
    except ValueError:
        pass

    if prlctl_bin is not None:
        command = [prlctl_bin, 'list', '--full', '--all', '--json']
        rc, out, err = module.run_command(command)
        if rc != 0:
            module.warn('Failed to gather Parallels virtual machine facts')

        else:
            data['VMs'] = json.loads(out)
            data['running_vm_count'] = len([vm for vm in data['VMs'] if vm['status'] == 'running'])


def main():
    module = AnsibleModule(
        argument_spec={},
        supports_check_mode=True,
    )

    results = {'ansible_facts': {}}
    parallels_data = {
        'Version': {
            'Edition': '',
            'Full': '',
            'Major': '',
            'MajorMinor': '',
            'Release': '',
        },
        'VMs': [],
        'running_vm_count': 0,
    }

    get_server_info(module, parallels_data)
    get_vm_info(module, parallels_data)

    parallels_data['sdk_version'] = get_sdk_version()
    results['ansible_facts']['parallels'] = parallels_data

    module.exit_json(**results)


if __name__ == '__main__':
    main()
