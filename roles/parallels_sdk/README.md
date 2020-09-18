Parallels SDK
=============

Install the Parallels Python SDK.

Requirements
------------

Parallels Desktop
Python

Role Variables
--------------

| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `parallels_sdk_version` | `524288` | SDK version. |
| `parallels_sdk_filename` | `ParallelsVirtualizationSDK-{{ parallels_app_version }}-mac.dmg` | Parallels SDK installer file name. |
| `parallels_sdk_url` | `{{ _parallels_base_url }}/{{ parallels_sdk_filename }}` | URL to download the SDK installer file from. |
| `parallels_sdk_file` | `{{ parallels_install_cache }}/{{ parallels_sdk_filename }}` | Path and filename of the downloaded SDK file. |


Dependencies
------------

`samdoran.macos.python` (or Python already installed by some other means)
`samdoran.macos.parallels`

Example Playbook
----------------

    - hosts: all
      roles:
        - samdoran.macos.python
        - samdoran.macos.parallels
        - samdoran.macos.parallels_sdk

License
-------

Apache 2.0
