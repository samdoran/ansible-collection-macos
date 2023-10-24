[![Galaxy](https://img.shields.io/badge/galaxy-samdoran.macos-blue)](https://galaxy.ansible.com/ui/repo/published/samdoran/macos/)

[![🧪 GitHub Actions CI/CD workflow tests badge]][GHA workflow runs list]
[![pre-commit.ci status badge]][pre-commit.ci results page]
[![Codecov badge]][Codecov coverage page]

Various roles and modules meant to be used on macOS.

## Roles ##

- `samdoran.macos.command_line_tools` - Install Xcode command line tools
- `samdoran.macos.homebrew` - Install Homebrew and manage taps, packages, and Cask apps
- `samdoran.macos.parallels` - Install Parallels Desktop
- `samdoran.macos.parallels_sdk` - Install the Parallels Python SDK
- `samdoran.macos.python` - Install Python from Python.org

## Modules ##

- `samdoran.macos.bootstrap_certs` - Generates a trusted root certificate authority store for use by the Python version that comes from Python.org using the certificate authorities found in the system keychain.
- `samdoran.macos.parallels_facts` - Gathers various facts from Parallels running on the host.
- `samdoran.macos.parallels_desktop` - Manage the state of Parallels Desktop.


[🧪 GitHub Actions CI/CD workflow tests badge]:
https://github.com/samdoran/ansible-collection-macos/actions/workflows/ansible-test.yml/badge.svg?branch=main&event=push
[GHA workflow runs list]:
https://github.com/samdoran/ansible-collection-macos/actions/workflows/ansible-test.yml?query=branch%3Amain

[pre-commit.ci results page]:
https://results.pre-commit.ci/latest/github/samdoran/ansible-collection-macos/main
[pre-commit.ci status badge]:
https://results.pre-commit.ci/badge/github/samdoran/ansible-collection-macos/main.svg

[Codecov badge]: https://img.shields.io/codecov/c/github/samdoran/ansible-collection-macos
[Codecov coverage page]: https://codecov.io/gh/samdoran/ansible-collection-macos
