"""A Yale Doorman Device instance."""
from __future__ import annotations

import logging
from typing import Any
from typing import cast
from typing import Dict
from typing import TYPE_CHECKING

from .const import AUTOLOCK_DISABLE
from .const import AUTOLOCK_ENABLE
from .const import BASE_URL
from .const import CONFIG_AUTOLOCK_IDX
from .const import CONFIG_LANG_IDX
from .const import CONFIG_VOLUME_IDX
from .const import STATUS_CODES
from .const import YALE_LOCK_STATE_LOCKED
from .const import YALE_LOCK_STATE_UNLOCKED

if TYPE_CHECKING:  # pragma: no cover
    from pyyaledoorman.client import Client

_LOGGER = logging.getLogger(__name__)


class Device:
    """Used to instantiate a Yale Doorman device."""

    def __init__(self, client: "Client", device_config: Dict[str, str]) -> None:
        """Initializes a Yale Doorman `Device`.

        Maps API responses to `Device` attributes.
        """
        self._device_config = device_config
        self._name = device_config["name"]
        self._id = device_config["device_id"]
        self._state = device_config["status_open"][0]
        self._type = device_config["type"]

        self._area = device_config["area"]
        self._address = device_config["address"]
        self._config = device_config["minigw_configuration_data"]

        try:
            self._mingw_status = int(device_config["minigw_lock_status"], 10)
        except Exception:  # pragma: no cover
            _LOGGER.debug("Couldnt parse mingw lock status", exc_info=True)

        self._client = client

    def _get_config_option(self, idx: str) -> str:
        index = int(idx, 10)
        parts = [self._config[i : i + 2] for i in range(0, len(self._config), 2)]
        return parts[index - 1]

    @property
    def volume_level(self) -> str:
        """Returns volume level.

        Returns:
            The configured volume level. Possible values are:
            `VOLUME_HIGH`,  `VOLUME_LOW`, `VOLUME_OFF`
        """
        return self._get_config_option(CONFIG_VOLUME_IDX)

    @property
    def language(self) -> str:
        """Returns volume level.

        Returns:
            The configured language of the device.
            `LANG_EN`, `LANG_DA`, `LANG_NO`, `LANG_SE`, `LANG_FI`, `LANG_RU`, `LANG_TR`.
        """
        return self._get_config_option(CONFIG_LANG_IDX)

    @property
    def autolock_status(self) -> str:
        """Returns the API status of whether autolock is enabled or not.

        Returns:
            * `FF` if autolock is enabled.
            * `00` if autolock is disabled.
        """
        return self._get_config_option(CONFIG_AUTOLOCK_IDX)

    @property
    def is_open(self) -> bool:
        """Returns `True` if the door is open. Otherwise `False`."""
        if self._mingw_status == 20:
            return True
        return False

    @property
    def is_locked(self) -> bool:
        """Returns `True` if the lock is locked. Otherwise `False`."""
        if self.state == YALE_LOCK_STATE_LOCKED:
            return True
        return False

    @property
    def area(self) -> str:
        """Returns the device area."""
        return self._area

    @property
    def address(self) -> str:
        """Returns the device address, most times synonymous with `device_id`."""
        return self._address

    @property
    def type(self) -> str:
        """Returns the type of the device.

        Only `device_type.door_lock` is supported at the time being
        """
        return self._type

    @property
    def state(self) -> str:
        """Returns the state of the device.

        For locks the state is usually one of:
        * `device_status.lock`
        * `device_status.unlock`
        """
        return self._state

    @property
    def name(self) -> str:
        """Returns the name of the device."""
        return self._name

    @property
    def device_id(self) -> str:
        """Returns the device ID."""
        return self._id

    async def lock(self) -> Dict[str, Any]:
        """Lock the lock and update the internal state to `YALE_LOCK_STATE_LOCKED`.

        Returns:
            Raw API response
        """
        await self._client.validate_access_token()
        params = {
            "area": self.area,
            "device_sid": self.address,
            "device_type": self.type,
            "zone": 1,
            "request_value": "1",
        }
        url = f"{BASE_URL}/api/panel/device_control/"
        async with self._client.session.post(
            url, data=params, raise_for_status=True
        ) as resp:
            data: Dict[str, str] = await resp.json()
            if data.get("code") == STATUS_CODES["SUCCESS"]:
                self._state = YALE_LOCK_STATE_LOCKED
            else:
                _LOGGER.debug("Couldnt lock the door. Unspecified error.")
            return data

    async def unlock(self, pincode: str) -> Dict[str, str]:
        """Unlocks the lock. Takes `pincode` as a required parameter to unlock.

        Arguments:
            pincode: a valid Yale Doorman pincode

        Returns:
             The API response.
        """
        await self._client.validate_access_token()
        url = f"{BASE_URL}/api/minigw/unlock/"
        params = {"area": self.area, "zone": 1, "pincode": pincode}

        async with self._client.session.post(
            url, data=params, raise_for_status=True
        ) as resp:
            data: Dict[str, str] = await resp.json()
            if data.get("code") == STATUS_CODES["SUCCESS"]:
                self._state = YALE_LOCK_STATE_UNLOCKED
            else:
                _LOGGER.debug("Couldnt unlock the door. Unspecified error.")
            return data

    async def enable_autolock(self) -> Dict[str, str]:
        """Enables autolocking of the lock."""
        return await self.update_deviceconfig(CONFIG_AUTOLOCK_IDX, AUTOLOCK_ENABLE)

    async def disable_autolock(self) -> Dict[str, str]:
        """Disables autolocking of the lock."""
        return await self.update_deviceconfig(CONFIG_AUTOLOCK_IDX, AUTOLOCK_DISABLE)

    async def get_deviceconfig(self) -> Dict[str, str]:
        """Fetches the device configuration.

        Returns:
            The raw API response.
        """
        url = f"{BASE_URL}/api/minigw/lock/config/"
        async with self._client.session.get(url, raise_for_status=True) as resp:
            return cast(Dict[str, str], await resp.json())

    async def update_deviceconfig(self, config_idx: str, value: str) -> Dict[str, str]:
        """Update device configuration.

        Arguments:
            config_idx: index of the confiuration option to change.
            value: new value to write.

        Returns:
            Raw API results.
        """
        url = f"{BASE_URL}/api/minigw/lock/config/"
        params = {"area": self.area, "zone": 1, "idx": config_idx, "val": value}
        async with self._client.session.post(
            url, data=params, raise_for_status=True
        ) as resp:
            return cast(Dict[str, str], await resp.json())

    async def update_state(self) -> None:
        """Updates the `Device` status from the API."""
        await self._client.validate_access_token()
        url = f"{BASE_URL}/api/panel/cycle/"
        async with self._client.session.get(url, raise_for_status=False) as resp:
            data = await resp.json()
            if data.get("message") == "OK!":
                devices = data.get("data", {}).get("device_status", [])
                for device in devices:
                    if device.get("device_id") == self.device_id:
                        self._state = device.get("status_open")[0]
                        try:
                            self._mingw_status = int(
                                device.get("minigw_lock_status"), 10
                            )
                        except TypeError:  # pragma: no cover
                            pass

            else:
                raise Exception("Unknown error")
