#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import re
import ssl
import tempfile

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils._text import to_bytes

DOCUMENTATION = """
---
module:
author:
    - Sam Doran (@samdoran)
version_added: '2020-08-03'
short_description: Bootstrap CA file using macOS system cerots
notes: []
description:
    - Get valid CAs from macOS system keychain and use them to build a CA file for use by Python
options: {}
"""

EXAMPLES = """
"""

RETURN = """
"""


def file_is_different(file, certs):
    try:
        with open(file, 'rb') as f:
            b_current_data = f.read()
    except OSError:
        # File does not exist
        return True

    if b_current_data.rstrip(b'\n') == to_bytes('\n'.join(certs)):
        return False

    return True


def write_file(module, path, certs):
    changed = False

    certs[:] = [i + '\n' for i in certs]
    if not module.check_mode:
        tmpfd, tmpfile = tempfile.mkstemp()
        with os.fdopen(tmpfd, 'w') as fd:
            fd.writelines(certs)

        module.atomic_move(tmpfile, path)

        file_args = {
            'path': path,
            'owner': 'root',
            'group': 'wheel',
            'mode': 0o0644,
            'secontext': None,
            'attributes': None,
        }
        changed = module.set_fs_attributes_if_different(file_args, changed)

    return changed


def get_certs(module, keychains):
    """ Get CA files from the keychain files """

    try:
        security_bin = get_bin_path('security')
    except ValueError:
        module.fail_json("Unable to find 'security'")

    cert_re = re.compile(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----', re.DOTALL)
    certs = []
    for keychain in module.params['keychains']:
        command = [security_bin, 'find-certificate', '-a', '-p', keychain]
        rc, out, err = module.run_command(command)
        matches = cert_re.findall(out)
        if matches:
            certs.extend(matches)

    return certs


def validate_certs(module, certs):
    valid_certs = []

    # # Validate certs
    # rc, out, err = module.run_command(command)

    try:
        openssl_bin = module.get_bin_path('openssl')
    except ValueError:
        module.fail_json("Unable to find 'openssl'")

    command = [openssl_bin, 'x509', '-inform', 'pem', '-checkend', '0', '-noout']
    for cert in certs:
        rc, out, err = module.run_command(command, data=cert)

        if rc == 0:
            valid_certs.append(cert)

    return valid_certs


def main():

    module = AnsibleModule(
        argument_spec={
            'keychains': {'type': 'list', 'default': ['/System/Library/Keychains/SystemRootCertificates.keychain']},
        },
        supports_check_mode=True,
    )

    results = {
        'changed': False,
    }

    # Get path and filename expected by ssl library
    openssl_cafile_path = ssl.get_default_verify_paths().openssl_cafile

    certs = get_certs(module, module.params['keychains'])
    valid_certs = validate_certs(module, certs)

    if file_is_different(openssl_cafile_path, valid_certs):
        results['changed'] = write_file(module, openssl_cafile_path, valid_certs)

    results['openssl_cafile'] = openssl_cafile_path

    module.exit_json(**results)


if __name__ == '__main__':
    main()
