Python for macOS from Python.org
================================

Install Python for macOS using the official installer from [Python.org](https://www.python.org/downloads/release/latest).

Requirements
------------

If compiling `libyaml`, Xcode command line tools must be installed.

Role Variables
--------------
| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `macos_python_version` | `3.8.6` | Python version to install. Check the [latest Python releases](https://www.python.org/downloads/release/latest) for valid version numbers. |
| `macos_python_packages` | `[]` | Additional Python packages to be installed with `pip`. |
| `macos_python_compile_libyaml` | `yes` | Whether or not to compile `libyaml`. This will speed up PyYAML. |
| `macos_python_libyaml_version` | `0.2.5` | Version of `libyaml` to download and compile. |
| `macos_python_cleanup_temp_files` | `yes` | Whether or not to remove installation files such as the Python installer and `libyaml` source code. |
| `macos_python_pip_extra_args` | `['--user']` | List of extra arguments passed to `pip`. |

Example Playbook
----------------

    - hosts: macs
      roles:
        - samdoran.macos.command_line_tools
        - samdoran.macos.python


License
-------

Apache 2.0
