"""Tests for pyyaledoorman."""
import json
from typing import Generator

import pytest
from aiohttp import ClientSession
from aioresponses import aioresponses
from pyyaledoorman import Client
from pyyaledoorman.client import AuthenticationError
from pyyaledoorman.const import AUTOLOCK_ENABLE
from pyyaledoorman.const import BASE_URL
from pyyaledoorman.const import LANG_EN
from pyyaledoorman.const import STATUS_CODES
from pyyaledoorman.const import VOLUME_OFF
from pyyaledoorman.const import YALE_LOCK_STATE_LOCKED

login_data = {
    "scope": "google_profile groups basic_profile write read",
    "expires_in": 259200,
    "access_token": "suchaccesstoken",
    "refresh_token": "suchrefreshtoken",
    "token_type": "Bearer",
}


@pytest.fixture
def mock_aioresponse() -> Generator[aioresponses, None, None]:
    """Setup for various mocked API calls."""
    with aioresponses() as mocked:
        mocked.post(f"{BASE_URL}/o/token/", status=200, payload=login_data, repeat=True)
        mocked.post(f"{BASE_URL}/api/panel/", status=200, repeat=True)
        mocked.post(f"{BASE_URL}/minigw/lock/config/", status=200)
        mocked.post(f"{BASE_URL}/api/minigw/lock/config/", status=200)
        mocked.get(
            f"{BASE_URL}/api/minigw/lock/config/",
            status=200,
            payload=json.load(open("tests/get_deviceconfig.json")),
        )
        mocked.get(
            f"{BASE_URL}/api/panel/device_status/",
            payload=json.load(open("tests/get_devices.json")),
            status=200,
            repeat=True,
        )
        mocked.get(
            f"{BASE_URL}/api/panel/cycle/",
            payload=json.load(open("tests/update_state.json")),
            status=200,
            repeat=False,
        )
        mocked.get(
            f"{BASE_URL}/api/panel/cycle/",
            payload={"message": "error"},
            status=403,
        )
        mocked.post(
            f"{BASE_URL}/api/panel/device_control/",
            payload=json.load(open("tests/lock.json")),
            status=200,
            repeat=False,
        )
        mocked.post(
            f"{BASE_URL}/api/panel/device_control/",
            payload=json.load(open("tests/lock_fail.json")),
            status=200,
            repeat=False,
        )
        mocked.post(
            f"{BASE_URL}/api/minigw/unlock/",
            payload=json.load(open("tests/unlock.json")),
            status=200,
            repeat=False,
        )
        mocked.post(
            f"{BASE_URL}/api/minigw/unlock/",
            payload=json.load(open("tests/unlock_fail.json")),
            status=200,
            repeat=False,
        )
        yield mocked


async def test_login(mock_aioresponse: aioresponses) -> None:
    """Test logging in to the API."""
    m = mock_aioresponse
    m.clear()
    m.post(f"{BASE_URL}/o/token/", status=200, payload=login_data, repeat=False)
    m.post(f"{BASE_URL}/o/token/", status=403, payload=login_data, repeat=False)
    m.post(f"{BASE_URL}/o/token/", status=403, reason="NO", repeat=False)
    yale = Client("test", "test", "test")
    await yale.login()
    assert yale.token == login_data["access_token"]
    assert yale.refresh_token == login_data["refresh_token"]
    await yale.validate_access_token()
    yale.login_ts = yale.login_ts - yale.token_expires_in - 1001
    with pytest.raises(AuthenticationError, match=r".*Check credentials*"):
        await yale.validate_access_token()


async def test_yale_nosession(mock_aioresponse: aioresponses) -> None:
    """Test logging in and basic checks without creating a new `ClientSession`."""
    yale = Client("test", "test", "test")

    await yale.login()

    await yale.update_devices()
    for device in yale.devices:
        data = await device.lock()
        assert data.get("code") == STATUS_CODES["SUCCESS"]
        assert data.get("data").get("device_sid") == device.device_id
        assert data.get("data").get("device_type") == device.type
        data = await device.unlock("123456")
        assert data.get("code") == STATUS_CODES["SUCCESS"]
        assert device.volume_level == VOLUME_OFF
        assert device.autolock_status == AUTOLOCK_ENABLE
        assert device.language == LANG_EN
    await yale._session.close()


async def test_get_deviceconfig(mock_aioresponse: aioresponses) -> None:
    """Verify that the device config can be fetched."""
    yale = Client("test", "test", "test")
    await yale.login()
    await yale.update_devices()
    assert len(yale.devices) == 1
    for device in yale.devices:
        await device.get_deviceconfig()


async def test_update_twice(mock_aioresponse: aioresponses) -> None:
    """Test running the update twice, check that you still have just one device."""
    yale = Client("test", "test", "test")
    await yale.login()
    await yale.update_devices()
    assert len(yale.devices) == 1
    for device in yale.devices:
        assert device.name == "door"
    await yale.update_devices()
    assert len(yale.devices) == 1
    mock_aioresponse.clear()

    mock_aioresponse.get(
        f"{BASE_URL}/api/panel/cycle/",
        payload=json.load(open("tests/update_state.json")),
        status=200,
        repeat=True,
    )
    data = json.load(open("tests/get_devices.json"))
    data["data"][0]["device_id"] = "another id!"
    mock_aioresponse.get(
        f"{BASE_URL}/api/panel/device_status/",
        payload=data,
        status=200,
        repeat=True,
    )
    await yale.update_devices()
    assert len(yale.devices) == 2
    await yale.update_devices()
    assert len(yale.devices) == 2


async def test_open(mock_aioresponse: aioresponses) -> None:
    """Test the `is_open` logic."""
    yale = Client("test", "test", "test")
    await yale.login()
    await yale.update_devices()

    for device in yale.devices:
        assert device._mingw_status == 35  # locked and closed
        assert device.is_locked is True
        assert device.is_open is False
        device._mingw_status = 20
        assert device.is_open is True


async def test_enable_autolock(mock_aioresponse: aioresponses) -> None:
    """Test enabling autolock."""
    yale = Client("test", "test", "test")
    await yale.login()
    await yale.update_devices()
    for device in yale.devices:
        await device.enable_autolock()


async def test_disable_autolock(mock_aioresponse: aioresponses) -> None:
    """Test disabling autolock."""
    yale = Client("test", "test", "test")
    await yale.login()
    await yale.update_devices()
    for device in yale.devices:
        await device.disable_autolock()


async def test_getdevices_fail(mock_aioresponse: aioresponses) -> None:
    """Test locking."""
    yale = Client("test", "test", "test")
    await yale.login()
    mock_aioresponse.clear()
    mock_aioresponse.get(
        f"{BASE_URL}/api/panel/device_status/",
        payload=json.load(open("tests/update_device_fail.json")),
        status=200,
    )
    await yale.update_devices()
    assert len(yale.devices) == 0


async def test_lock(mock_aioresponse: aioresponses) -> None:
    """Test locking."""
    mock_aioresponse.get(
        f"{BASE_URL}/api/panel/device_status/",
        payload=json.load(open("tests/get_devices.json")),
        status=200,
        repeat=True,
    )
    yale = Client("test", "test", "test")
    await yale.login()
    await yale.update_devices()
    for device in yale.devices:
        data = await device.lock()
        assert data.get("code") == STATUS_CODES["SUCCESS"]
        assert data.get("data").get("device_sid") == device.device_id
        assert data.get("data").get("device_type") == device.type
        assert device.is_locked is True
        assert device.state == YALE_LOCK_STATE_LOCKED
        assert device._mingw_status == 35
        data = await device.lock()
        assert data.get("code") == STATUS_CODES["ERROR"]


async def test_unlock(mock_aioresponse: aioresponses) -> None:
    """Test unlocking."""
    yale = Client("test", "test", "test")
    await yale.login()
    await yale.update_devices()
    for device in yale.devices:
        data = await device.unlock("123456")
        assert data.get("code") == STATUS_CODES["SUCCESS"]
        assert device.is_locked is False
        data = await device.unlock("123456")
        assert data.get("code") == STATUS_CODES["ERROR"]


async def test_update_device_fail(mock_aioresponse: aioresponses) -> None:
    """Test updates that fail."""
    yale = Client("test", "test", "test")

    await yale.login()
    await yale.update_devices()
    for device in yale.devices:
        assert device.state == YALE_LOCK_STATE_LOCKED
        await device.update_state()
        assert device.state == YALE_LOCK_STATE_LOCKED
        with pytest.raises(Exception, match=r".*Unknown error.*"):
            await device.update_state()
    await yale._session.close()


async def test_update_device(mock_aioresponse: aioresponses) -> None:
    """Test updating the device status."""
    yale = Client("test", "test", "test")

    await yale.login()
    await yale.update_devices()
    for device in yale.devices:
        assert device.state == YALE_LOCK_STATE_LOCKED
        await device.update_state()
        assert device.state == YALE_LOCK_STATE_LOCKED
    await yale._session.close()


async def test_yale_session(mock_aioresponse: aioresponses) -> None:
    """Verify that passing a `ClientSession` object works."""
    session = ClientSession()
    yale = Client("test", "test", "test", session)

    await yale.login()
    assert yale.token == login_data["access_token"]
    await yale.update_devices()
    assert yale.login_ts is not None
    assert yale.token_expires_in is not None

    assert len(yale.devices) == 1
    for device in yale.devices:
        assert device.name == "door"
    await yale._session.close()
