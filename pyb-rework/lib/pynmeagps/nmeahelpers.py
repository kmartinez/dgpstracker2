"""
Collection of NMEA helper methods which can be used
outside the NMEAMessage or NMEAReader classes

Created on 04 Mar 2021

:author: semuadmin
:copyright: SEMU Consulting © 2021
:license: BSD 3-Clause
"""

from datetime import datetime
from pynmeagps.nmeatypes_core import NMEA_MSGIDS, NMEA_MSGIDS_PROP, LA, LN
import pynmeagps.exceptions as nme

KNOTSCONV = {"MS": 0.5144447324, "FS": 1.68781084, "MPH": 1.15078, "KMPH": 1.852001}


def int2hexstr(val: int) -> str:
    """
    Convert integer to hex string representation.

    :param int val: integer < 255 e.g. 31
    :return: hex representation of integer e.g. '1F'
    :rtype: str
    """

    return format(val, "02X")


def get_parts(message: object) -> tuple:
    """
    Get talker, msgid, payload and checksum of raw NMEA message.

    :param object message: entire message as bytes or string
    :return: tuple of (talker as str, msgID as str, payload as list, checksum as str)
    :rtype: tuple
    :raises: NMEAMessageError (if message is badly formed)
    """

    try:
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        content, cksum = message.strip("$\r\n").split("*", 1)
        hdr, payload = content.split(",", 1)
        payload = payload.split(",")
        if hdr[0:1] == "P":  # proprietary
            talker = "P"
            msgid = hdr[1:]
        else:  # standard
            talker = hdr[0:2]
            msgid = hdr[2:]
        return talker, msgid, payload, cksum
    except Exception as err:
        raise nme.NMEAMessageError(f"Badly formed message {message}") from err


def get_content(message: object) -> str:
    """
    Get content of raw NMEA message (everything between "$" and "*").

    :param object message: entire message as bytes or string
    :return: content as str
    :rtype: str
    """

    if isinstance(message, bytes):
        message = message.decode("utf-8")
    content, _ = message.strip("$\r\n").split("*", 1)
    return content


def list2csv(payload: list) -> str:
    """
    Convert list of strings to single string of comma separated values.

    :param list payload: list of values e.g. ["this", "that"]
    :return: string of comma separated values e.g. "this,that"
    :rtype: str
    """

    return ",".join(map(str, payload))


def calc_checksum(message: object) -> str:
    """
    Calculate checksum for raw NMEA message.

    :param object message: entire message as bytes or string
    :return: checksum as hex string
    :rtype: str
    """

    content = get_content(message)
    cksum = 0
    for sub in content:
        cksum ^= ord(sub)
    return int2hexstr(cksum)


def isvalid_cksum(message: object) -> bool:
    """
    Validate raw message checksum.

    :param bytes message: entire message as bytes or string
    :return: checksum valid flag
    :rtype: bool
    """

    _, _, _, cksum = get_parts(message)
    return cksum == calc_checksum(message)


def dmm2ddd(pos: str, att: str) -> float:
    """
    Convert NMEA lat/lon string to (unsigned) decimal degrees.

    :param str pos: (d)ddmm.mmmmm
    :param str att: 'LA' (lat) or 'LN' (lon)
    :return: pos as decimal degrees
    :rtype: float

    """

    try:
        if att == LA:
            posdeg = float(pos[0:2])
            posmin = float(pos[2:])
        else:
            posdeg = float(pos[0:3])
            posmin = float(pos[3:])
        return round((posdeg + posmin / 60), 10)
    except (TypeError, ValueError):
        return ""


def ddd2dmm(degrees: float, att: str, hpmode: bool = False) -> str:
    """
    Convert decimal degrees to native NMEA degrees decimal
    minutes string (NB: standard NMEA only supports 5dp
    minutes precision - a high precision mode offers 7dp
    precision but this may not be accepted by all NMEA parsers).

    :param float degrees: degrees
    :param str att: 'LA' (lat) or 'LN' (lon)
    :param bool hpmode: high precision mode (7dp rather than 5dp)
    :return: degrees as (d)ddmm.mmmmm(mm) formatted string
    :rtype: str

    """

    try:
        degrees = abs(degrees)
        degrees, minutes = divmod(degrees * 60, 60)
        degrees = int(degrees * 100)
        if hpmode:
            if att == "LA":
                dmm = f"{degrees + minutes:.7f}".zfill(12)
            else:  # LN
                dmm = f"{degrees + minutes:.7f}".zfill(13)
        else:
            if att == "LA":
                dmm = f"{degrees + minutes:.5f}".zfill(10)
            else:  # LN
                dmm = f"{degrees + minutes:.5f}".zfill(11)
        return dmm
    except (TypeError, ValueError):
        return ""


def date2utc(dates: str) -> datetime.date:
    """
    Convert NMEA Date to UTC datetime.

    :param str dates: NMEA date ddmmyy
    :return: UTC date YYyy:mm:dd
    :rtype: datetime.date
    """

    try:
        utc = datetime.strptime(dates, "%d%m%y")
        return utc.date()
    except (TypeError, ValueError):
        return ""


def time2utc(times: str) -> datetime.time:
    """
    Convert NMEA Time to UTC datetime.

    :param str times: NMEA time hhmmss.ss
    :return: UTC time hh:mm:ss.ss
    :rtype: datetime.time
    """

    try:
        if len(times) == 6:  # decimal seconds is omitted
            times = times + ".00"
        utc = datetime.strptime(times, "%H%M%S.%f")
        return utc.time()
    except (TypeError, ValueError):
        return ""


def time2str(tim: datetime.time) -> str:
    """
    Convert datetime.time to NMEA formatted string.

    :param datetime.time tim: time
    :return: NMEA formatted time string hhmmss.ss
    :rtype: str
    """

    try:
        return tim.strftime("%H%M%S.%f")[0:9]
    except (AttributeError, TypeError, ValueError):
        return ""


def date2str(dat: datetime.date) -> str:
    """
    Convert datetime.date to NMEA formatted string.

    :param datetime.date dat: date
    :return: NMEA formatted date string ddmmyy
    :rtype: str
    """

    try:
        return dat.strftime("%d%m%y")
    except (AttributeError, TypeError, ValueError):
        return ""


def deg2dms(degrees: float, att: str) -> str:
    """
    Convert decimal degrees to degrees minutes seconds string
    e.g. '51°20′45.6″N'

    :param float degrees: degrees
    :param str att: 'LA' (lat) or 'LN' (lon)
    :return: degrees as d.m.s formatted string
    :rtype: str

    """

    try:
        negative = degrees < 0
        degrees = abs(degrees)
        minutes, seconds = divmod(degrees * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        if negative:
            sfx = "S" if att == "LA" else "W"
        else:
            sfx = "N" if att == "LA" else "E"
        return f"{int(degrees)}\u00b0{int(minutes)}\u2032{round(seconds,5)}\u2033{sfx}"
    except (TypeError, ValueError):
        return ""


def deg2dmm(degrees: float, att: str) -> str:
    """
    Convert decimal degrees to degrees decimal minutes string
    e.g. '51°20.76′S'.

    :param float degrees: degrees
    :param str att: 'LA' (lat) or 'LN' (lon)
    :return: degrees as dm.m formatted string
    :rtype: str

    """

    try:
        negative = degrees < 0
        degrees = abs(degrees)
        degrees, minutes = divmod(degrees * 60, 60)
        if negative:
            sfx = "S" if att == "LA" else "W"
        else:
            sfx = "N" if att == "LA" else "E"
        return f"{int(degrees)}\u00b0{round(minutes,7)}\u2032{sfx}"
    except (TypeError, ValueError):
        return ""


def knots2spd(knots: float, unit: str = "MS") -> float:
    """
    Convert speed in knots to speed in specified units.

    :param float knots: knots
    :param unit str: 'MS' (default), 'FS', MPH', 'KMPH'
    :return: speed in m/s, feet/s, mph or kmph
    :rtype: float

    """

    try:
        return knots * KNOTSCONV[unit.upper()]
    except KeyError as err:
        raise KeyError(
            f"Invalid conversion unit {unit.upper()} - must be in {list(KNOTSCONV.keys())}."
        ) from err
    except TypeError as err:
        raise TypeError(
            f"Invalid knots value {knots} - must be float or integer."
        ) from err


def msgdesc(msgID: str) -> str:
    """
    Return descriptive string for NMEA msgId.

    :param msgID str: message ID e.g. 'GGA'
    :return: description of message
    :rtype: str

    """
    # pylint: disable=invalid-name

    if msgID in NMEA_MSGIDS:
        return NMEA_MSGIDS[msgID]
    if msgID in NMEA_MSGIDS_PROP:
        return NMEA_MSGIDS_PROP[msgID]
    return f"Unknown msgID {msgID}"
