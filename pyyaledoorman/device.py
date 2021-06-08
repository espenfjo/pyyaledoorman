"""A Yale Doorman Device instance."""
from __future__ import annotations

import logging
from typing import cast
from typing import Dict
from typing import TYPE_CHECKING

from .const import AUTOLOCK_DISABLE
from .const import AUTOLOCK_ENABLE
from .const import BASE_URL
from .const import CONFIG_IDX_AUTOLOCK
from .const import CONFIG_IDX_LANG
from .const import CONFIG_IDX_VOLUME
from .const import STATUS_CODES
from .const import YALE_LOCK_STATE_LOCKED
from .const import YALE_LOCK_STATE_UNLOCKED

if TYPE_CHECKING:  # pragma: no cover
    from pyyaledoorman.client import Client

_LOGGER = logging.getLogger(__name__)


class Device:
    """Used to instantiate a Yale Doorman device."""

    def __init__(self, client: "Client", device_config: Dict[str, str]) -> None:
        """Initialize a Yale Doorman `Device`.

        Maps API responses to `Device` attributes.
        """
        self.parse_config(device_config)
        self._client = client

    def parse_config(self, device_config: Dict[str, str]) -> None:
        """Parse API responses and sets `Device` configuration."""
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

    def _get_config_option(self, idx: str) -> str:
        index = int(idx, 10)
        parts = [self._config[i : i + 2] for i in range(0, len(self._config), 2)]
        return parts[index - 1]

    @property
    def volume_level(self) -> str:
        """Return volume level.

        Returns:
            The configured volume level. Possible values are:
            `VOLUME_HIGH`,  `VOLUME_LOW`, `VOLUME_OFF`
        """
        return self._get_config_option(CONFIG_IDX_VOLUME)

    @property
    def language(self) -> str:
        """Return audio language.

        Returns:
            The configured language of the device. Possible value are:
            `LANG_EN`, `LANG_DA`, `LANG_NO`, `LANG_SE`, `LANG_FI`, `LANG_RU`, `LANG_TR`.
        """
        return self._get_config_option(CONFIG_IDX_LANG)

    @property
    def autolock_enabled(self) -> bool:
        """Return whether autolock is enabled.

        Returns:
            bool: `True` if autolock is enabled, otherwise `False`
        """
        state = self._get_config_option(CONFIG_IDX_AUTOLOCK)
        if state == "FF":
            return True
        return False

    @property
    def is_open(self) -> bool:
        """Return `True` if the door is open. Otherwise `False`."""
        if self._mingw_status == 20:
            return True
        return False

    @property
    def is_locked(self) -> bool:
        """Return `True` if the lock is locked. Otherwise `False`."""
        if self.state == YALE_LOCK_STATE_LOCKED:
            return True
        return False

    @property
    def area(self) -> str:
        """Return the device area."""
        return self._area

    @property
    def address(self) -> str:
        """Return the device address, most times synonymous with `device_id`."""
        return self._address

    @property
    def type(self) -> str:
        """Return device type.

        Only `device_type.door_lock` is supported at the time being
        """
        return self._type

    @property
    def state(self) -> str:
        """Return device state.

        For locks the state is usually one of:
        * `device_status.lock`
        * `device_status.unlock`
        """
        return self._state

    @property
    def name(self) -> str:
        """Return the device name."""
        return self._name

    @property
    def device_id(self) -> str:
        """Return the device ID."""
        return self._id

    async def lock(self) -> bool:
        """Lock the lock and update the internal state to `YALE_LOCK_STATE_LOCKED`.

        Returns:
            bool: True if locking was successful, False otherwise.
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
            url, data=params, headers=self._client.headers, raise_for_status=True
        ) as resp:
            data: Dict[str, str] = await resp.json()
            if data.get("code") == STATUS_CODES["SUCCESS"]:
                self._state = YALE_LOCK_STATE_LOCKED
                return True
            else:
                _LOGGER.debug("Couldnt lock the door. Unspecified error.")
            return False

    async def unlock(self, pincode: str) -> bool:
        """Unlocks the lock. Takes `pincode` as a required parameter to unlock.

        Arguments:
            pincode: a valid Yale Doorman pincode

        Returns:
             bool: True if unlock successful, False otherwise.
        """
        await self._client._validate_access_token()
        url = f"{BASE_URL}/api/minigw/unlock/"
        params = {"area": self.area, "zone": 1, "pincode": pincode}

        async with self._client.session.post(
            url, data=params, headers=self._client.headers, raise_for_status=True
        ) as resp:
            data: Dict[str, str] = await resp.json()
            if data.get("code") == STATUS_CODES["SUCCESS"]:
                self._state = YALE_LOCK_STATE_UNLOCKED
                return True
            else:
                _LOGGER.debug("Couldnt unlock the door. Unspecified error.")
            return False

    async def enable_autolock(self) -> bool:
        """Enable autolocking of the lock.

        Return:
            bool: `True` if successful, `False` otherwise.
        """
        if await self.set_deviceconfig(CONFIG_IDX_AUTOLOCK, AUTOLOCK_ENABLE):
            self._update_deviceconfig(CONFIG_IDX_AUTOLOCK, AUTOLOCK_ENABLE)
            return True
        return False  # pragma: no cover

    async def disable_autolock(self) -> bool:
        """Disable autolocking of the lock.

        Return:
            bool: `True` if successful, `False` otherwise.
        """
        if await self.set_deviceconfig(CONFIG_IDX_AUTOLOCK, AUTOLOCK_DISABLE):
            self._update_deviceconfig(CONFIG_IDX_AUTOLOCK, AUTOLOCK_DISABLE)
            return True
        return False  # pragma: no cover

    def _update_deviceconfig(self, index: str, value: str) -> None:
        """Fetch the device configuration.

        Arguments:
            index: The index of the configuration string to update.
            value: Value to write to the configuration string. Usually a `short`.
        """
        idx = int(index, 10)
        parts = [self._config[i : i + 2] for i in range(0, len(self._config), 2)]
        parts[idx - 1] = value
        self._config = "".join(parts)

    async def get_deviceconfig(self) -> Dict[str, str]:
        """Fetch the device configuration.

        Returns:
            The raw API response.
        """
        url = f"{BASE_URL}/api/minigw/lock/config/"
        async with self._client.session.get(
            url, headers=self._client.headers, raise_for_status=True
        ) as resp:
            return cast(Dict[str, str], await resp.json())

    async def set_deviceconfig(self, config_idx: str, value: str) -> bool:
        """Set device configuration.

        Arguments:
            config_idx: index of the confiuration option to change.
            value: new value to write.

        Returns:
            bool: True if the device config was updated successfully, False otherwise.
        """
        url = f"{BASE_URL}/api/minigw/lock/config/"
        params = {"area": self.area, "zone": 1, "idx": config_idx, "val": value}
        async with self._client.session.post(
            url, data=params, headers=self._client.headers, raise_for_status=True
        ) as resp:
            data = await resp.json()
            if data.get("code") == STATUS_CODES["SUCCESS"]:
                return True
            return False  # pragma: no cover

    async def update_state(self) -> None:
        """Update the `Device` status from the API."""
        await self._client.validate_access_token()
        url = f"{BASE_URL}/api/panel/cycle/"
        async with self._client.session.get(
            url, headers=self._client.headers, raise_for_status=False
        ) as resp:
            data = await resp.json()
            if data.get("code") == STATUS_CODES["SUCCESS"]:
                devices = data.get("data", {}).get("device_status", [])
                for device in devices:
                    if device.get("device_id") == self.device_id:
                        self.parse_config(device)

            else:
                raise Exception("Unknown error")
