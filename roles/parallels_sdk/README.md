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
| `` | `` |  |


Dependencies
------------

`samdoran.macos.parallels`

Example Playbook
----------------

    - hosts: all
      roles:
         - samdoran.macos.parallels
         - samdoran.macos.parallels_sdk

License
-------

Apache 2.0
