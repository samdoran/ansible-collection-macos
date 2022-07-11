Xcode Command Line Tools
========================

Install Xcode command line tools.

Since macOS >= 12.3 does not ship with Python, the `bootstrap.yml` playbook included with this collection can be used to install the system Python from Apple in addition to the Xcode command line tools. Running playbooks from collections requires Ansible >= 2.11.

    ansible-playbook -i inventory.yml samdoran.macos.bootstrap

The playbook targets a group called `macos_12_plus_hosts`, falling back to `all`. This can be overridden using an extra var.

    ansible-playbook -i inventory.yml -e macos_12_plus_hosts=my_custom_group samdoran.macos.bootstrap

A standalone script for installing the command line tools is included in the `scripts/` directory for reference or running locally.

Requirements
------------

None

Role Variables
--------------

| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `macos_cli_python_interpreter` | `/usr/bin/python3` | Python interpreter used for verifying correct installation of Python from Apple. |

Example Playbook
----------------

Using the role with the default tasks file requires Python to already be installed.

    - hosts: macs
      roles:
         - samdoran.macos.command_line_tools

For a new macOS system that does not have Python installed, this role must be run with fact gathering disabled. Fact gathering requires Python on the managed node and runs before any tasks in the play.

This is the `bootstrap.yml` playbook included with the `samdoran.macos` collection.

    - hosts: macs
      gather_facts: no
      become: yes

      tasks:
        - import_role:
            name: samdoran.macos.command_line_tools
            tasks_from: bootstrap.yml


License
-------

Apache 2.0
