"""Test the elro connects cloud API for authentication."""

# pylint: disable=line-too-long,redefined-outer-name,protected-access


from unittest.mock import AsyncMock, patch

import json
import pytest

from elro.auth import ElroConnectsSession

MOCK_AUTH_RESPONSE = {
    "access_token": "eyasdfklasdfjalskdfjlasdggffghdfghdf.edsfgsdhJHDkdaskjdksdfyJ1aWQiOiI3OTQ5NjdfghdfghdfghdfghdfghdfghdghfghhgfhhfghfgdhfdgfghdfghzOCwianRpIjoiYTBkNzQxMTctZDQxNi00ZmUwLWI2YWEtNTMxOGUzY2QxYWM3Iiwicm9sZXMiOltdfSAg.B9ESpw7LFzHRFWxrtF44iX3CDNuQcYYAP0BQSZwN_nqOCETsa1xFq961klvPhkfHYilhJWDTqZygNyfYQJUwvg==",
    "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiI3OTQ5NjQ0OTI0NSIsInBpZCI6IjAxMjg4MTU0MTQ2IiwidHlwZSI6IkFQUCIsImV4cCI6MTY2MTg1OTkzOCwianRpIjoiMjcxYzg1ZDEtMTE3MS00MTJlLThkMjktNzhiNDRjYjZiMTU1Iiwicm9sZXMiOltdLCJhdGkiOiJhMGQ3NDExNy1kNDE2LTRmZTAtYjZhYS01MzE4ZTNjZDFhYzcifSAg.K3nUsdfgsdfgsdfgsdfgsdfhghfjjfghjfghjfghjfghjdghjdfhfdghdfghdfghsdfgsdfhfgdghdfghdfghh==",
    "expires_in": 86400,
    "token_type": "bearer",
    "user": "79123456789",
}

MOCK_DEVICE_RESPONSE = [
    {
        "ctrlKey": "deadbeefdeadbeefdeadbeefdeadbeef",
        "devTid": "ST_deadbeef0000",
        "devType": "INDEPENDENT",
        "mid": "0123456789ab",
        "bindKey": "beefdead012345678beefdead0123456",
        "workModeType": "JSON_CTRL",
        "ssid": "HEKR-TEST",
        "rssi": None,
        "mac": "deadbeef012",
        "gis": {
            "ip": {
                "country": None,
                "province": None,
                "city": "内网IP",
                "citycode": None,
                "district": None,
                "adcode": None,
                "township": None,
                "towncode": None,
                "street": None,
                "ip": "10.0.0.1",
            },
            "geo": None,
            "bs": None,
            "bsOther": None,
        },
        "dcInfo": {
            "fromDC": "fra",
            "dc": None,
            "area": "",
            "fromArea": "eu",
            "remoteDomain": "hekreu.me",
            "domain": "hekr.me",
            "connectHost": "fra-hub.hekreu.me",
        },
        "lanIp": None,
        "devKey": None,
        "lanIpUpdateDate": 1658855873540,
        "binVersion": "2.0.3.30",
        "binType": "B",
        "sdkVer": "2.0.3.30",
        "mcuVer": None,
        "ownerUid": "79123456789",
        "granted": False,
        "forceBind": False,
        "productPublicKey": "k0wfHypbzGlO9coR3asomepublickeyOSuZM332invalidkeyfffwadffwqQT/wP2",
        "logo": "https://allinone-ufile.hekr.me/category/a52db783-bb20-4e64-ba5f-76f7cf2bd4fd/door1.png",
        "androidH5Page": "",
        "iosH5Page": "",
        "weChatH5Page": "",
        "webH5Page": None,
        "iosPageZipURL": None,
        "androidPageZipURL": None,
        "weChatPageZipURL": None,
        "webPageZipURL": None,
        "productBand": "",
        "model": "188A",
        "cidName": "家居家装/报警器",
        "categoryName": {"zh_CN": "家居家装/报警器", "en_US": "Misc/Alarm"},
        "productName": {
            "zh_CN": "我的家",
            "en_US": "My Home",
            "de_DE": "Mein Zuhause",
            "fr_FR": "Chez moi",
            "es_ES": "Mi hogar",
        },
        "online": True,
        "bindResultCode": None,
        "bindResultMsg": None,
        "quickOperationConfigList": [],
        "deviceSort": -1,
        "deviceName": "My Home",
        "name": "My Home",
        "desc": None,
        "folderSort": -1,
        "features": None,
        "folderId": "0",
        "folderName": "root",
        "showType": "COMMON",
        "subDevices": [],
    }
]

MOCK_USER = "test@example.com"
MOCK_PASSWORD = "somepassword"


@pytest.fixture
def mock_get():
    """Mock aiohttp get and post requests."""
    with patch("aiohttp.ClientSession.get") as mock_session_get:
        yield mock_session_get


@pytest.fixture
def mock_post():
    """Mock aiohttp get and post requests."""
    with patch("aiohttp.ClientSession.post") as mock_session_post:
        yield mock_session_post


class CloudTest(ElroConnectsSession):
    """Demo with cloud login."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize the demo."""
        self._username = username
        self._password = password
        ElroConnectsSession.__init__(self)

    async def help_async_fetch_data(self) -> None:
        """Log in and fetch data."""
        await self.async_login(self._username, self._password)
        print(f"user (id): {self.session['user']}")
        print(f"access_token: {self.session['access_token']}")
        print(f"last_login: {self.session['last_login']}")
        connector_list = await self.async_get_connectors()
        for connector in connector_list:
            print(connector["dev_id"])
            print(connector["sw_version"])
            print(connector["online"])


@pytest.mark.asyncio
async def test_login_and_get_device_info(mock_get, mock_post):
    """Test the login and fetch info."""
    mock_post.return_value.__aenter__.return_value.json = AsyncMock(
        side_effect=[MOCK_AUTH_RESPONSE]
    )
    mock_get.return_value.__aenter__.return_value.json = AsyncMock(
        side_effect=[MOCK_DEVICE_RESPONSE]
    )

    # Setup session and login
    cloud_session = ElroConnectsSession()
    await cloud_session.async_login(MOCK_USER, MOCK_PASSWORD)

    assert cloud_session.session["user"] == MOCK_AUTH_RESPONSE["user"]
    assert cloud_session.session["access_token"] == MOCK_AUTH_RESPONSE["access_token"]
    assert cloud_session.session["last_login"]

    connector_list = await cloud_session.async_get_connectors()
    assert connector_list[0]["dev_id"] == MOCK_DEVICE_RESPONSE[0]["devTid"]
    assert connector_list[0]["sw_version"] == MOCK_DEVICE_RESPONSE[0]["binVersion"]
    assert connector_list[0]["online"] is True


@pytest.mark.asyncio
async def test_get_device_info_without_login(mock_get):
    """Test the login and fetch info."""
    mock_get.return_value.__aenter__.return_value.json = AsyncMock(
        side_effect=[MOCK_DEVICE_RESPONSE]
    )

    # Setup session
    cloud_session = ElroConnectsSession()
    with pytest.raises(ValueError):
        await cloud_session.async_get_connectors()
