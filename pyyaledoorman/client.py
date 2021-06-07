"""Yale API Client. Used to log in to the API and instantiate Devices."""
import logging
from datetime import datetime
from http.client import FORBIDDEN
from http.client import UNAUTHORIZED
from typing import Any
from typing import List
from typing import Optional

from aiohttp import ClientSession

from .const import BASE_URL
from .const import INITIAL_TOKEN
from .const import STATUS_CODES
from .device import Device

_LOGGER = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Exception for authentication errors."""

    def __init__(self, *args: Any) -> None:
        """Initialize the Exception."""
        Exception.__init__(self, *args)


class Client:
    """Yale Doorman client.

    Arguments:
        username: Username for logging in to the Yale API.
        password: Password for logging in to the Yale API.
        initial_token: Initial token for logging in to the Yale API.
        session (optional): aiohttp ClientSession to use.
    """

    def __init__(
        self,
        username: str,
        password: str,
        initial_token: str = INITIAL_TOKEN,
        session: Optional[ClientSession] = None,
    ) -> None:
        """Initialize the Yale Doorman Client."""
        self.username = username
        self.password = password
        self.initial_token = initial_token
        self.logged_in = datetime.timestamp(datetime.now())
        _LOGGER.info("Logged in to Yale")
        if session:
            self._session = session
            self._managed_session = False
        else:
            self._session = ClientSession()
            self._managed_session = True
        self._last_conf_update: Optional[datetime] = None
        self._devices: List[Device] = []
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    @property
    def login_ts(self) -> float:
        """Return the login timestamp."""
        return self._login_ts

    @login_ts.setter
    def login_ts(self, timestamp: float) -> None:
        """Set the login timestamp.

        Arguments:
            timestamp: Timestamp of whence the API was logged in to.
        """
        self._login_ts = timestamp

    @property
    def token(self) -> Optional[str]:
        """Return the access token."""
        return self._token

    @token.setter
    def token(self, _token: str) -> None:
        """Set the access token."""
        self._token = _token
        self._session.headers.add("Authorization", f"Bearer {self.token}")

    @property
    def refresh_token(self) -> Optional[str]:
        """Return the refresh token."""
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, _refresh_token: Optional[str]) -> None:
        """Set the refresh token."""
        self._refresh_token = _refresh_token

    @property
    def token_expires_in(self) -> int:
        """Return seconds from login whence the access token expires."""
        return self._token_expires_in

    @token_expires_in.setter
    def token_expires_in(self, expires: int) -> None:
        """Set number of seconds since login when the access token expires."""
        self._token_expires_in = expires

    @property
    def devices(self) -> List[Device]:
        """Return list of Devices."""
        return self._devices

    @property
    def session(self) -> ClientSession:
        """Return the aiohttp session."""
        return self._session

    async def login(self) -> bool:  # raises: AuthenticationError
        """Log in to the Yale API.

        Returns:
            bool: True if successfully logged in.

        Raises:
            AuthenticationError: Supplied username, password or initial token is wrong.
        """
        _LOGGER.info("Trying to log in to Yale..")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {self.initial_token}",
        }
        if self.refresh_token:
            auth_data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            }
        else:
            auth_data = {
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            }
        async with self._session.post(
            f"{BASE_URL}/o/token/",
            data=auth_data,
            headers=headers,
        ) as resp:
            status = resp.status
            data = await resp.json()

            if status in (FORBIDDEN, UNAUTHORIZED):
                if self.refresh_token:
                    self.refresh_token = None
                    return await self.login()
                _LOGGER.debug(
                    "Failed to authenticate with Yale Smart Alarm. Error: %s", data
                )
                raise AuthenticationError(
                    "Failed to authenticate with Yale Smart Alarm. Check credentials."
                )
            self.token_expires_in = data.get("expires_in")

            self.login_ts = datetime.timestamp(datetime.now())
            self.token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            return True

    async def validate_access_token(self) -> None:
        """Verify that our access token is still valid."""
        now = datetime.now()
        timestamp = datetime.timestamp(now)
        # Check if login time + expires in is past now(-ish)
        if (self.login_ts + self.token_expires_in) <= (timestamp - 1000):
            await self.login()

    async def update_devices(self) -> None:
        """Update the device states."""
        await self.validate_access_token()
        url = f"{BASE_URL}/api/panel/device_status/"
        async with self._session.get(url, raise_for_status=False) as resp:
            res = await resp.json()
            if res.get("code") == STATUS_CODES["SUCCESS"]:
                for device in res.get("data"):
                    existing = False
                    for existing_device in self._devices:
                        if existing_device.device_id == device.get("device_id"):
                            existing = True
                            await existing_device.update_state()
                            break
                    if existing:
                        continue

                    self._devices.append(Device(self, device))
            else:
                _LOGGER.debug("Couldn't fetch devices. Unknown error!")
