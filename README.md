[![Galaxy](https://img.shields.io/badge/galaxy-samdoran.macos-blue)](https://galaxy.ansible.com/samdoran/macos)


Various roles and modules meant to be used on macOS.

## Roles ##

`samdoran.macos.command_line_tools` - Install Xcode command line tools
`samdoran.macos.homebrew` - Install Homebrew and manage taps, packages, and Cask apps
`samdoran.macos.parallels` - Install Parallels Desktop
`samdoran.macos.parallels_sdk` - Install the Parallels Python SDK
`samdoran.macos.python` - Install Python from Python.org

## Modules ##

`samdoran.macos.hostname` - A fork of the Ansible `hostname` module that adds support for macOS.
`samdoran.macos.bootstrap_certs` - Generates a trusted root certificate authority store for use by the Python version that comes from Python.org using the certificate authorities found in the system keychain.
`parallels_facts` - Gathers various facts from Parallels running on the host.
