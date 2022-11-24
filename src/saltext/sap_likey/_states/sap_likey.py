"""
SaltStack extension for saplikey
Copyright (C) 2022 SAP UCC Magdeburg

SAP NetWeaver AS ABAP License Key state module
==============================================
SaltStack module that implements states based on saplikey functionality.

:codeauthor:    Benjamin Wegener, Alexander Wilke
:maturity:      new
:depends:       requests
:platform:      Linux

This module implements states that utilize ``saplikey`` functionality. The command line tool is
part of the SAP NetWeaver AS ABAP Kernel and allows license key management from the command line.

.. note::
    This module can only run on linux platforms.
"""
import logging


# Globals
log = logging.getLogger(__name__)

__virtualname__ = "sap_likey"


# pylint: disable=unused-argument
def license_present(name, filename=None, remove_other_sid=True, remove_other_hwkey=True, **kwargs):
    """
    Ensure that the license keys defined in a file are present in the system

    name
        SID of the SAP system.

    filename
        Full path to the license file, default is None. If no filename is given, a temporary license
        will be installed if no valid license is present in the system.

    remove_other_sid
        Remove licenses that are not assigned to the SID (default is ``True``).

    remove_other_hwkey
        Remove licenses that are not assigned to the current hardware key (default is ``True``).

    Example:

    .. code-block:: jinja

        License for SAP System S4H is installed:
          sap_likey.license_present:
            - name: S4H
            - filename: /tmp/S4H.txt
    """
    log.debug("Running function")
    ret = {"name": name, "changes": {"old": [], "new": []}, "comment": "", "result": True}
    log.debug("Retrieving system info")
    info = __salt__["sap_likey.info"](sid=name)
    log.debug("Retrieving installed licenses")
    licenses_system = __salt__["sap_likey.show"](sid=name)
    if remove_other_sid:
        log.debug(f"Removing licenses not assigned to {name}")
        for lic in licenses_system:
            if lic["system"] != name:
                log.debug(f"Found license assigned to {lic['system']}, removing")
                if __opts__["test"]:
                    msg = (
                        f"SAP system license {lic['system']} / "
                        f"{lic['hardware_key']} / {lic['software_product']} would be removed"
                    )
                    ret["changes"]["old"].append(msg)
                else:
                    success = __salt__["sap_likey.delete"](name=lic["system"], sid=name)
                    if success:
                        msg = (
                            f"SAP system license {lic['system']} / "
                            f"{lic['hardware_key']} / {lic['software_product']}"
                        )
                        ret["changes"]["old"].append(msg)
                    else:
                        ret["comment"] = (
                            f"Could not remove license for SAP system license {lic['system']} "
                            f"/ {lic['hardware_key']} / {lic['software_product']}"
                        )
                        ret["result"] = False
                        return ret
    if remove_other_hwkey:
        log.debug(f"Removing licenses not assigned to hardware_key {info['hardware_key']}")
        for lic in licenses_system:
            if lic["hardware_key"] != info["hardware_key"]:
                log.debug(f"Found license assigned to {lic['hardware_key']}, removing")
                if __opts__["test"]:
                    msg = (
                        f"SAP system license {lic['system']} / {lic['hardware_key']} "
                        f"/ {lic['software_product']} would be removed"
                    )
                    ret["changes"]["old"].append(msg)
                else:
                    success = __salt__["sap_likey.delete"](
                        name=lic["system"], sid=name, hwkey=lic["hardware_key"]
                    )
                    if success:
                        msg = (
                            f"SAP system license {lic['system']} / {lic['hardware_key']} "
                            f"/ {lic['software_product']}"
                        )
                        ret["changes"]["old"].append(msg)
                    else:
                        ret["comment"] = (
                            f"Could not remove license for system {lic['system']} / {lic['hardware_key']} "
                            f"/ {lic['software_product']}"
                        )
                        ret["result"] = False
                        return ret
    if filename:
        log.debug(f"Reading license file {filename}")
        licenses_file = __salt__["sap_likey.read_lic_file"](filename=filename)
        # because there can be multiple licenses in one file, we need to check if ALL match
        all_valid = len(licenses_file) > 0
        for lic_file in licenses_file:
            found = False
            for lic_sys in licenses_system:
                # removing attributes that are not present in the license from file
                if "last_successful_check" in lic_sys:
                    del lic_sys["last_successful_check"]
                if "validity" in lic_sys:
                    del lic_sys["validity"]
                if "type_of_license_key" in lic_sys:
                    del lic_sys["type_of_license_key"]
                if lic_file == lic_sys:
                    found = True
                    break
            if not found:
                all_valid = False
                break
        if not all_valid:
            log.debug(f"Not all licenses are installed, removing all licenses for {name}")
            if __opts__["test"]:
                for lic in licenses_system:
                    msg = (
                        f"SAP system license {lic['system']} / {lic['hardware_key']} "
                        f"/ {lic['software_product']} would be removed"
                    )
                    ret["changes"]["old"].append(msg)
            else:
                success = __salt__["sap_likey.delete"](name=name, sid=name)
                if success:
                    for lic in licenses_system:
                        msg = (
                            f"SAP system license {lic['system']} / "
                            f"{lic['hardware_key']} / {lic['software_product']}"
                        )
                        ret["changes"]["old"].append(msg)
                else:
                    ret["comment"] = f"Could not remove license for system {name}"
                    ret["result"] = False
                    return ret
            # checking if the <sid>adm user can read the license file
            sidadm = f"{name.lower()}adm"
            if __salt__["file.get_user"](filename) != sidadm:
                log.debug(f"Ensuring that {sidadm} owns the license file")
                user_info = __salt__["user.info"](sidadm)
                if __opts__["test"]:
                    msg = (
                        f"Would change to owner of {filename} to uid {user_info['uid']} "
                        f"/ gid {user_info['gid']}"
                    )
                    ret["changes"]["new"].append(msg)
                else:
                    __salt__["file.chown"](
                        user=user_info["uid"], group=user_info["gid"], path=filename
                    )
            log.debug("Installing new licenses")
            if __opts__["test"]:
                for lic in licenses_file:
                    msg = (
                        f"SAP system license {lic['system']} / {lic['hardware_key']} "
                        f"/ {lic['software_product']} would be installed"
                    )
                    ret["changes"]["new"].append(msg)
            else:
                success = __salt__["sap_likey.install"](sid=name, filename=filename)
                if success:
                    for lic in licenses_file:
                        msg = (
                            f"SAP system license {lic['system']} / "
                            f"{lic['hardware_key']} / {lic['software_product']}"
                        )
                        ret["changes"]["new"].append(msg)
                else:
                    ret["comment"] = f"Could not install licenses for system {name}"
                    ret["result"] = False
                    return ret
            ret["comment"] = "Installed licenses"
        else:
            log.debug("All licenses are already installed correctly")
    else:
        log.debug("No license file defined, checking for a valid license and removing all others")
        valid_license = False
        for lic in licenses_system:
            # skip maintenance licenses
            if lic["software_product"].startswith("Maintenance_"):
                continue
            if lic["validity"] == "valid":
                valid_license = True
                break
        if not valid_license:
            if licenses_system:
                msg = "No valid license defined, removing all licenses and adding temporary one"
                log.debug(msg)
                if __opts__["test"]:
                    ret["changes"]["old"].append(f"SAP system {name} license would be deleted")
                else:
                    success = __salt__["sap_likey.delete"](name=name, sid=name)
                    if success:
                        ret["changes"]["old"].append(f"SAP system {name} license")
                    else:
                        ret["comment"] = f"Could not remove license for system {name}"
                        ret["result"] = False
                        return ret
            log.debug(f"Adding temporary license for {info['software_products']}")
            if __opts__["test"]:
                msg = (
                    f"SAP system {name} temporary license for {info['software_products']} "
                    "would be added"
                )
                ret["changes"]["new"].append(msg)
            else:
                success = __salt__["sap_likey.temp"](sid=name, product=info["software_products"])
                if success:
                    msg = f"SAP system {name} temporary license for {info['software_products']}"
                    ret["changes"]["new"].append(msg)
                else:
                    ret["comment"] = (
                        f"Could not add temporay license for system {name} "
                        f"for {info['software_products']}"
                    )
                    ret["result"] = False
                    return ret
        else:
            ret["comment"] = f"System {name} already has a valid license"

    if not ret["changes"].get("new") and not ret["changes"].get("old"):
        ret["changes"] = {}
        ret["comment"] = "No changes required"

    ret["result"] = True if (not __opts__["test"] or not ret["changes"]) else None

    return ret


# pylint: disable=unused-argument
def license_absent(name, remove_all=True, **kwargs):
    """
    Ensure that a SAP license is absent from an SAP system.

    name
        SID of the SAP system.

    remove_all
        Set to True to remove all licenses, default is ``True``.

    Example:

    .. code-block:: jinja

        All licenses for SAP System S4H are absent:
          sap_likey.license_absent:
            - name: S4H
            - remove_all: True
    """
    log.debug("Running function")
    ret = {"name": name, "changes": {"old": [], "new": []}, "comment": "", "result": True}
    licenses_system = __salt__["sap_likey.show"](sid=name)
    for lic_sys in licenses_system:
        if remove_all or lic_sys["system"] == name:
            log.debug(f"Removing license for {lic_sys['system']}")
            if __opts__["test"]:
                msg = (
                    f"SAP system license {lic_sys['system']} / {lic_sys['hardware_key']} "
                    f"/ {lic_sys['software_product']} would be removed"
                )
                ret["changes"]["old"].append(msg)
            else:
                success = __salt__["sap_likey.delete"](
                    name=name,
                    sid=name,
                    hwkey=lic_sys["hardware_key"],
                    product=lic_sys["software_product"],
                )
                if success:
                    msg = (
                        f"SAP system license {lic_sys['system']} / {lic_sys['hardware_key']} "
                        f"/ {lic_sys['software_product']}"
                    )
                    ret["changes"]["old"].append(msg)
                else:
                    ret["comment"] = (
                        f"Could not remove license for {lic_sys['system']} / "
                        f"{lic_sys['hardware_key']} / {lic_sys['software_product']}"
                    )
                    ret["result"] = False
                    return ret
    if not ret["changes"].get("new") and not ret["changes"].get("old"):
        ret["changes"] = {}
        ret["comment"] = "No changes required"

    ret["result"] = True if (not __opts__["test"] or not ret["changes"]) else None

    return ret
