"""
SaltStack extension for saplikey
Copyright (C) 2022 SAP UCC Magdeburg

saplikey execution module
=========================
SaltStack execution module that wraps ``saplikey`` functions.

:codeauthor:    Benjamin Wegener, Alexander Wilke
:maturity:      new
:depends:       N/A
:platform:      Linux

This module wraps different functions of the ``saplikey`` command line tool.

.. note::
    This module was only tested on linux platforms.
"""
import logging
import re

import salt.utils.files
import salt.utils.platform

# Third Party libs

# Globals

log = logging.getLogger(__name__)

__virtualname__ = "sap_likey"


def __virtual__():
    """
    Only work on POSIX-like systems
    """
    if salt.utils.platform.is_windows():
        return False, "This module doesn't work on Windows."
    return __virtualname__


def _get_saplikey_path(sidadm):
    """
    Retrieve the path to the ``saplikey`` binary
    """
    dir_library = __salt__["cmd.shell"](cmd="echo $DIR_LIBRARY", runas=sidadm)
    if not dir_library or "/" not in dir_library:
        raise Exception(f"Cannot retrieve $DIR_LIBRARY for user {sidadm}")
    return f"{dir_library}/saplikey"


# pylint: disable=unused-argument
def info(sid, **kwargs):
    """
    Wrapper for the saplikey function ``get``. Retrieves system license information.

    sid
        SID of the SAP NetWeaver systems.

    Returns list of dictonaries of the license keys.

    CLI Example:

    .. code-block:: bash

        salt "*" sap_likey.info sid="S4H"
    """
    log.debug("Running function")
    sid = sid.upper()
    runas = f"{sid.lower()}adm"
    saplikey_exec = _get_saplikey_path(runas)
    log.debug(f"Running with user {runas} and using executable {saplikey_exec}")

    cmd = f"{saplikey_exec} pf=/sapmnt/{sid}/profile/DEFAULT.PFL -get"
    log.trace(f"Executing '{cmd}'")
    cmd_ret = __salt__["cmd.run_all"](cmd, runas=runas, timeout=30)
    log.debug(f"Output:\n{cmd_ret}")
    if cmd_ret.get("retcode") != 0:
        out = cmd_ret.get("stderr").strip()
        log.error(f"Could not show licenses:\n{out}")
        return False

    lines = cmd_ret.get("stdout").split("\n")
    ifo = {}
    for i in range(0, len(lines)):  # pylint: disable=consider-using-enumerate
        if ":" in lines[i]:
            key, value = lines[i].split(":", 1)
            key = key.lower().replace(".", "").strip().replace(" ", "_")
            key = re.sub("_+", "_", key)
            value = value.strip().split(" ")[0]
            ifo[key] = value
    return ifo


# pylint: disable=unused-argument
def show(sid, **kwargs):
    """
    Wrapper for the saplikey function ``show``. Retrieves all SAP licenses.

    sid
        SID of the SAP NetWeaver systems.

    Returns list of dictonaries of the license keys.

    CLI Example:

    .. code-block:: bash

        salt "*" sap_likey.show sid="S4H"
    """
    log.debug("Running function")
    sid = sid.upper()
    runas = f"{sid.lower()}adm"
    saplikey_exec = _get_saplikey_path(runas)
    log.debug(f"Running with user {runas} and using executable {saplikey_exec}")

    cmd = f"{saplikey_exec} pf=/sapmnt/{sid}/profile/DEFAULT.PFL -show"
    log.trace(f"Executing '{cmd}'")
    cmd_ret = __salt__["cmd.run_all"](cmd, runas=runas, timeout=30)
    log.debug(f"Output:\n{cmd_ret}")
    if cmd_ret.get("retcode") != 0:
        out = cmd_ret.get("stderr").strip()
        log.error(f"Could not show licenses:\n{out}")
        return False

    lines = cmd_ret.get("stdout").split("\n")
    licenses = []
    for i in range(0, len(lines)):  # pylint: disable=consider-using-enumerate
        if lines[i].endswith("License Key:"):
            i += 2
            lic = {}
            while lines[i]:
                key, value = lines[i].split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                key = re.sub("_+", "_", key)
                value = value.strip()
                lic[key] = value
                i += 1
            licenses.append(lic)

    return licenses


# pylint: disable=unused-argument
def install(sid, filename, **kwargs):
    """
    Wrapper for the saplikey function ``install``. Install SAP licenses from a file.

    sid
        SID of the SAP NetWeaver systems.

    filename
        Full path of the license file to install.

    Returns ``(True|False)``

    CLI Example:

    .. code-block:: bash

        salt "*" sap_likey.install sid="S4H" filename="/tmp/S4H.txt"
    """
    log.debug("Running function")
    sid = sid.upper()
    runas = f"{sid.lower()}adm"
    saplikey_exec = _get_saplikey_path(runas)
    log.debug(f"Running with user {runas} and using executable {saplikey_exec}")

    cmd = f"{saplikey_exec} pf=/sapmnt/{sid}/profile/DEFAULT.PFL -install {filename}"
    log.trace(f"Executing '{cmd}'")
    cmd_ret = __salt__["cmd.run_all"](cmd, runas=runas, timeout=30)
    log.debug(f"Output:\n{cmd_ret}")
    if cmd_ret.get("retcode") != 0:
        out = cmd_ret.get("stderr").strip()
        log.error(f"Could not show licenses:\n{out}")
        return False
    return True


# pylint: disable=unused-argument
def delete(name, sid, hwkey="*", product="*", **kwargs):
    """
    Wrapper for the saplikey function ``delete``. Delete SAP licenses.

    name
        Name of the license to delete. This is the SID of the system for which the license
        was installed.

    sid
        SID of the SAP NetWeaver system.

    hwkey
        Hardware key, default is ``*``.

    product
        Product key, e.g. NetWeaver_HDB or Maintenance_HDB, default is ``*``.

    Returns ``(True|False)``

    CLI Example:

    .. code-block:: bash

        salt "*" sap_likey.delete name="M70" sid="S4H"

    .. note::
        The arguments ``hwkey`` and ``product`` support globbing.
    """
    log.debug("Running function")
    sid = sid.upper()
    runas = f"{sid.lower()}adm"
    saplikey_exec = _get_saplikey_path(runas)
    log.debug(f"Running with user {runas} and using executable {saplikey_exec}")

    cmd = f"{saplikey_exec} pf=/sapmnt/{sid}/profile/DEFAULT.PFL -delete {name} {hwkey} {product}"
    log.trace(f"Executing '{cmd}'")
    cmd_ret = __salt__["cmd.run_all"](cmd, runas=runas, timeout=30)
    log.debug(f"Output:\n{cmd_ret}")
    if cmd_ret.get("retcode") != 0:
        out = cmd_ret.get("stderr").strip()
        log.error(f"Could not delete licenses:\n{out}")
        return False
    return True


# pylint: disable=unused-argument
def temp(sid, product, **kwargs):
    """
    Wrapper for the saplikey function ``temp``. Installs a temporary SAP license.

    sid
        SID of the SAP NetWeaver systems.

    product
        Product key, e.g. ``NetWeaver_HBD`` or ``Maintenance_HDB``.

    Returns ``(True|False)``

    CLI Example:

    .. code-block:: bash

        salt "*" sap_likey.temp sid="S4H" product="NetWeaver_HBD"

    .. note::
        The installation of temporary licenses is only supported if the system already
        had a valid license installed at some point in time.
    """
    log.debug("Running function")
    sid = sid.upper()
    runas = f"{sid.lower()}adm"
    saplikey_exec = _get_saplikey_path(runas)
    log.debug(f"Running with user {runas} and using executable {saplikey_exec}")

    cmd = f"{saplikey_exec} pf=/sapmnt/{sid}/profile/DEFAULT.PFL -temp {product}"
    log.trace(f"Executing '{cmd}'")
    cmd_ret = __salt__["cmd.run_all"](cmd, runas=runas, timeout=30)
    log.debug(f"Output:\n{cmd_ret}")
    if cmd_ret.get("retcode") != 0:
        out = cmd_ret.get("stderr").strip()
        log.error(f"Could not show licenses:\n{out}")
        return False
    return True


# pylint: disable=unused-argument
def read_lic_file(filename, **kwargs):
    """
    Reads a SAP license file and returns a dictionary with information, e.g. a text file
    with:

    .. code-block:: ini

        SAPSYSTEM=ZZZ
        HARDWARE-KEY=Z0000000000
        INSTNO=0020000000
        BEGIN=20220720
        EXPIRATION=99991231
        LKEY=*******
        SWPRODUCTNAME=NetWeaver_HDB
        SWPRODUCTLIMIT=2147483647
        SYSTEM-NR=000000000800000000

    filename
        Full path to the license file.

    CLI Example:

    .. code-block:: bash

        salt "*" sap_likey.read_lic_file filename="/tmp/S4H.txt"

    .. note::
        All keys (except LKEY) are converted to the same naming convention as in the
        ``saplikey`` function ``-show``.
    """
    log.debug("Running function")
    data = []
    with salt.utils.files.fopen(filename, "r") as fil:
        lines = fil.readlines()

    for i in range(0, len(lines)):  # pylint: disable=consider-using-enumerate
        if "Begin SAP License" in lines[i]:
            lic = {}
            i += 1
            while i < len(lines) and "=" in lines[i] and "Begin SAP License" not in lines[i]:
                key, value = lines[i].split("=", 1)
                value = value.strip()
                if key == "SAPSYSTEM":
                    lic["system"] = value
                elif key == "HARDWARE-KEY":
                    lic["hardware_key"] = value
                elif key == "INSTNO":
                    lic["installation_number"] = value
                elif key == "BEGIN":
                    lic["begin_of_validity"] = value
                elif key == "EXPIRATION":
                    lic["end_of_validity"] = value
                elif key == "SWPRODUCTNAME":
                    lic["software_product"] = value
                elif key == "SWPRODUCTLIMIT":
                    lic["software_product_limit"] = value
                elif key == "SYSTEM-NR":
                    lic["system_number"] = value
                i += 1
            data.append(lic)
        i += 1

    return data
