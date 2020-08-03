Homebrew
=========

Install  Homebrew, Homebrew command line tools, and Homebrew Cask GUI apps.

Requirements
------------

- `samdoran.macos.homebrew`

Role Variables
--------------
| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `homebrew_taps` | `[]` | List of Homebrew taps to add |
| `homebrew_packages` | `[]` | List of Homebrew packages to install |
| `homebrew_cask_apps` | `[]` | List of Homebrew Cask apps to install |
| `homebrew_tmp_path` | `/var/tmp/homebrew` | Directory used to download installation script. |
| `homebrew_cleanup_temp_files` | `yes` | Whether or not to remove the Hombrew installation script. |

Example Playbook
----------------

    - hosts: macs
      roles:
         - samdoran.macos.homebrew


License
-------

Apache 2.0
