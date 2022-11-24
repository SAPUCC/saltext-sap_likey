# SaltStack SAP NetWeaver license key extension
This SaltStack extensions allows managing license keys for SAP NetWeaver AS ABAP systems.

**THIS PROJECT IS NOT ASSOCIATED WITH SAP IN ANY WAY**

## Installation
Run the following to install the SaltStack SAP license key extension:
```bash
salt-call pip.install saltext.sap-likey
```
Keep in mind that this package must be installed on every minion that should utilize the states and execution modules.

Alternatively, you can add this repository directly over gitfs
```yaml
gitfs_remotes:
  - https://github.com/SAPUCC/saltext-sap_likey.git:
    - root: src/saltext/sap_likey
```
In order to enable this, logical links under `src/saltext/sap_likey/` from `_<dir_type>` (where the code lives) to `<dir_type>` have been placed, e.g. `_modules` -> `modules`. This will double the source data during build, but:
 * `_modules` is required for integrating the repo over gitfs
 * `modules` is required for the salt loader to find the modules / states

## Usage
A state using the SAP license key extension looks like this:
```jinja
License for SAP System S4H is installed:
  sap_likey.license_present:
    - name: S4H
    - filename: /tmp/S4H.txt
```

## Docs
See https://saltext-sap-likey.readthedocs.io/ for the documentation.

## Contributing
We would love to see your contribution to this project. Please refer to `CONTRIBUTING.md` for further details.

## License
This project is licensed under GPLv3. See `LICENSE.md` for the license text and `COPYRIGHT.md` for the general copyright notice.
