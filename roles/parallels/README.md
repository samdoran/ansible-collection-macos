Parallels
=========

Install Parallels Desktop using the mass depployment tool.

Requirements
------------

A valid Parallels license key.

Role Variables
--------------

| Name              | Default Value       | Description          |
|-------------------|---------------------|----------------------|
| `parallels_app_version` |  `16.0.0-48916` | Parallels version to download and install. |
| `parallels_install_cache` |  `/var/tmp/ParallelsInstall` | Directory used to storing the Parallels installer. |
| `parallels_autodeploy_url` |  `https://download.parallels.com/desktop/tools/pd-autodeploy.zip` | URL for downloading the Parallels autodeploy tool. |
| `parallels_licence_key` |  `~` | Parallels license key. |
| `parallels_max_termination_severity` |  `murdered` | One of `terminated`, `killed` or `murdered`. |
| `parallels_reboot_post_upgrade` |  `yes` | Reboot the host if yes, restart Parallels otherwise. |
| `parallels_assert_kexts` |  `no` | Require that Parallels hypervisor kernel extensions are allowed. |


Dependencies
------------

None.

Example Playbook
----------------

    - hosts: all
      roles:
         - samdoran.macos.parallels

License
-------

Apache 2.0
