"""Constants used by pyyaledoorman."""
from traitlets.utils.bunch import Bunch

BASE_URL = "https://mob.yalehomesystem.co.uk/yapi"
INITIAL_TOKEN = (
    "VnVWWDZYVjlXSUNzVHJhcUVpdVNCUHBwZ3ZPakxUeXNsRU1LUHBjdTpkd3RPb"  # noqa
    "E15WEtENUJ5ZW1GWHV0am55eGhrc0U3V0ZFY2p0dFcyOXRaSWNuWHlSWHFsWVBEZ1BSZE1xczF4R3V"
    "wVTlxa1o4UE5ubGlQanY5Z2hBZFFtMHpsM0h4V3dlS0ZBcGZzakpMcW1GMm1HR1lXRlpad01MRkw3MGR"
    "0bmNndQ=="
)

BITWISE_CLOSED = 16
BITWISE_LOCKED = 1

LOCK_STATES = Bunch(
    locked="device_status.lock",
    unlocked="device_status.unlock",
    failed="failed",
)


AUTOLOCK_DISABLE = "00"
AUTOLOCK_ENABLE = "FF"

CONFIG_IDX_AUTOLOCK = "02"
CONFIG_IDX_LANG = "05"
CONFIG_IDX_VOLUME = "01"

LANG_DA = "04"
LANG_EN = "01"
LANG_FI = "07"
LANG_NO = "05"
LANG_RU = "08"
LANG_SE = "06"
LANG_TR = "10"
STATUS_CODES = {"SUCCESS": "000", "ERROR": "997"}
VOLUME_HIGH = "03"
VOLUME_LOW = "02"
VOLUME_OFF = "01"
YALE_LOCK_STATE_DOOR_OPEN = "dooropen"
YALE_LOCK_STATE_LOCKED = "device_status.lock"
YALE_LOCK_STATE_UNLOCKED = "device_status.unlock"
