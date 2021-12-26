from typing import Final
from discord import Color

# ID
ADMIN_ID: Final[int] = 280855156608860160
TEST_SERVERS: Final[list[int]] = [911676954317582368, 855835632470458459, 881164190784565319]

# PATH
DEFAULT_BOT_CONFIG_PATH: Final[str] = "configs/bot.json"
DB_PATH: Final[str] = 'gamepad.db'
DUMP_PATH: Final[str] = 'dump.sql'

# KEYWORDS
CREATE: Final[str] = 'create'
EDIT: Final[str] = 'edit'
LIST: Final[str] = 'list'
DELETE: Final[str] = 'delete'
VIEW: Final[str] = 'view'

# COLOR
INITIAL_COLOR: Final[Color] = Color(0x2673e8)

# VALUES
# LFG_ALERT_PREV_MIN: Final[int] = 10
LFG_ALERT_PREV_SEC: Final[int] = 600
# MIN2SEC: Final[int] = 60
# HOUR2SEC: Final[int] = 60 * 60
DAY2SEC: Final[int] = 24 * 60 * 60
ID_SEP: Final[str] = ','

