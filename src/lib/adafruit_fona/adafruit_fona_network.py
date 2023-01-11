# SPDX-FileCopyrightText: 2020 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_fona_network`
=================================================================================

Interface for connecting to and interacting with GSM and CDMA cellular networks.
Modified for use with FONA MiniGSM. Should still work for other FONA boards as far as I know

* Author(s): Brent Rubell, Michael Jones

"""

try:
    from typing import Optional, Tuple, Type
    from types import TracebackType
    from adafruit_fona.adafruit_fona import FONA
except ImportError:
    pass

__version__ = "2.1.13"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FONA.git"

# Network types
NET_GSM = 0x01
NET_CDMA = 0x02


class CELLULAR:
    """Interface for connecting to and interacting with GSM and CDMA cellular networks.

    :param FONA fona: The Adafruit FONA module we are using.
    :param tuple apn: Tuple containing APN name, (optional) APN username,
                        and APN password.
    """

    def __init__(
        self, fona: FONA, apn: Tuple[str, Optional[str], Optional[str]]
    ) -> None:
        self._iface = fona
        self._apn = apn
        self._network_type = NET_CDMA

        if not self._iface.version == 0x4 or self._iface.version == 0x5:
            self._network_type = NET_GSM
            if not self._iface.version == 0x6:
                self._iface.gps = True

    def __enter__(self) -> "CELLULAR":
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[type]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.disconnect()

    @property
    def imei(self) -> str:
        """Returns the modem's IEMI number, as a string."""
        return self._iface.iemi

    @property
    def iccid(self) -> str:
        """Returns the SIM card's ICCID, as a string."""
        return self._iface.iccid

    @property
    def is_attached(self) -> bool:
        """Returns if the modem is attached to the network."""
        if self._network_type == NET_GSM:
            #for some reason the base driver checks gps status so i left it in but bypassed it for our module
            gps_check = -1
            if not self._iface.version == 6:
                gps_check = self._iface.gps
            else:
                gps_check = 3
            #status 1 = connected to home network, status 5 = connected and roaming
            if gps_check == 3 and (self._iface.network_status == 1 or self._iface.network_status == 5):
                return True
        else:  # Attach CDMA network
            if self._iface.ue_system_info == 1 and self._iface.network_status == 1:
                return True
        return False

    @property
    def is_connected(self):
        """Returns if attached to network and an IP Addresss was obtained."""
        if not (self.is_attached and self._iface.local_ip):
            return False
        return True

    def connect(self) -> None:
        """Connect to cellular network."""
        if not self._iface.set_gprs(self._apn, True):
            # reset context for next connection attempt
            self._iface.set_gprs(self._apn, False)

    def disconnect(self) -> None:
        """Disconnect from cellular network."""
        self._iface.set_gprs(self._apn, False)
