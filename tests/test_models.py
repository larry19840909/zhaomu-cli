from zhaomu.models.base import OperationResult, _from_dict
from zhaomu.models.region import Region
from zhaomu.models.product import CloudProduct, Image, CompareItem
from zhaomu.models.cloud.server import CloudServer, CloudServerDetail
from zhaomu.models.cloud.request import (
    OrderRequest, RenewRequest, UpgradeRequest, UpgradePriceRequest,
    RebuildRequest, ResetPasswordRequest, AutoRenewRequest, NoteRequest,
)
from zhaomu.models.accelerator import (
    Accelerator, AcceleratorOrderRequest, AcceleratorModifyRequest,
    AcceleratorPortRequest, TrafficUsage,
)
from zhaomu.models.balance import Balance


class TestOperationResult:
    def test_from_dict_success(self):
        data = {"success": True, "message": "ok"}
        r = OperationResult._from_dict(data)
        assert r.success is True
        assert r.message == "ok"
        assert r.info is None

    def test_from_dict_with_info(self):
        data = {"success": True, "message": "created", "info": {"id": 1}}
        r = OperationResult._from_dict(data)
        assert r.success is True
        assert r.message == "created"
        assert r.info == {"id": 1}

    def test_from_dict_failure(self):
        data = {"success": False, "message": "error occurred"}
        r = OperationResult._from_dict(data)
        assert r.success is False
        assert r.message == "error occurred"


class TestRegion:
    def test_from_dict(self):
        data = {
            "id": 3,
            "continent": "北美洲",
            "continentEn": "north-america",
            "country": "美国",
            "countryEn": "us",
            "area": "美西",
            "areaEn": "us-west",
            "province": "加州",
            "provinceEn": "california",
            "city": "洛杉矶",
            "cityEn": "los-angeles",
            "zone": "V",
        }
        r = Region._from_dict(data)
        assert r.id == 3
        assert r.city == "洛杉矶"
        assert r.cityEn == "los-angeles"
        assert r.country == "美国"
        assert r.continentEn == "north-america"

    def test_from_list(self):
        data = [{"id": 1, "city": "Tokyo"}, {"id": 2, "city": "Hong Kong"}]
        result = Region._from_list(data)
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].city == "Hong Kong"


class TestCloudProduct:
    def test_from_dict(self):
        data = {
            "id": 35,
            "cpu": 1,
            "ram": 1024,
            "disk": 25,
            "diskMax": 25,
            "diskData": 0,
            "diskDataMax": 40000,
            "diskMedia": "SSD",
            "bandwidth": None,
            "bandwidthMax": None,
            "traffic": 1000,
            "priceHour": 0.1,
            "price": 49,
            "priceQuarter": 147,
            "priceHalfYear": 294,
            "priceYear": 588,
            "tags": "",
            "outOfStock": 0,
            "noWindows": None,
            "region_id": 3,
        }
        p = CloudProduct._from_dict(data)
        assert p.id == 35
        assert p.cpu == 1
        assert p.ram == 1024
        assert p.diskMedia == "SSD"
        assert p.priceHour == 0.1
        assert p.price == 49


class TestImage:
    def test_from_dict(self):
        data = {"id": 5, "name": "CentOS 7 64位", "type": "CentOS"}
        img = Image._from_dict(data)
        assert img.id == 5
        assert img.name == "CentOS 7 64位"
        assert img.type == "CentOS"


class TestCompareItem:
    def test_from_dict(self):
        data = {"target_id": "1", "name": "实时开通", "explain": "支持"}
        item = CompareItem._from_dict(data)
        assert item.target_id == 1
        assert item.name == "实时开通"


class TestCloudServer:
    def test_from_dict(self):
        data = {
            "id": 21299, "ip": "155.138.139.237", "root": "root",
            "cpu": 1, "ram": 1024, "disk": 25, "diskData": 0,
            "diskMedia": "SSD", "bandwidth": None, "traffic": 1000,
            "image": "CentOS 7 64位", "renewPrice": 49, "paymentCycle": 1,
            "priceHour": None, "price": 49, "priceQuarter": 147,
            "priceHalfYear": 294, "priceYear": 588,
            "startTime": "2022-09-12 20:53:44", "endTime": "2022-11-12 20:53:44",
            "status": 2, "note": None, "noteUser": None, "isAutoRenew": 0,
            "region_id": 18,
        }
        s = CloudServer._from_dict(data)
        assert s.id == 21299
        assert s.ip == "155.138.139.237"
        assert s.status == 2
        assert s.image == "CentOS 7 64位"

    def test_from_list(self):
        data = [
            {"id": 1, "ip": "1.2.3.4", "status": 2},
            {"id": 2, "ip": "5.6.7.8", "status": 3},
        ]
        result = CloudServer._from_list(data)
        assert len(result) == 2
        assert result[1].status == 3


class TestCloudServerDetail:
    def test_from_dict_with_password(self):
        data = {
            "id": 21299, "ip": "155.138.139.237", "root": "root",
            "password": "secret123", "cpu": 1, "ram": 1024, "disk": 25,
            "status": 2, "region_id": 18,
        }
        d = CloudServerDetail._from_dict(data)
        assert d.id == 21299
        assert d.password == "secret123"


class TestCloudRequests:
    def test_order_request_to_dict(self):
        req = OrderRequest(productId=91, disk=40, diskData=0, bandwidth=0,
                           imageId=5, paymentCycle=1)
        d = req.to_dict()
        assert d["productId"] == 91
        assert d["disk"] == 40
        assert d["imageId"] == 5

    def test_renew_request_to_dict(self):
        req = RenewRequest(paymentCycle=2)
        assert req.to_dict() == {"paymentCycle": 2}

    def test_upgrade_request_to_dict(self):
        req = UpgradeRequest(productId=35, disk=None, diskData=None, bandwidth=None)
        d = req.to_dict()
        assert d == {"productId": 35}

    def test_rebuild_request_to_dict(self):
        req = RebuildRequest(imageId=13)
        assert req.to_dict() == {"imageId": 13}

    def test_reset_password_request_to_dict(self):
        req = ResetPasswordRequest(password="newpass")
        assert req.to_dict() == {"password": "newpass"}

    def test_auto_renew_request_to_dict(self):
        req = AutoRenewRequest(enable=1)
        assert req.to_dict() == {"enable": 1}

    def test_note_request_to_dict(self):
        req = NoteRequest(note="test server")
        assert req.to_dict() == {"note": "test server"}


class TestAccelerator:
    def test_from_dict(self):
        data = {
            "id": 1, "type": "基础版",
            "domain": "123.123.123.123_30896.ipssh.net",
            "region": "cn-sh2", "ip": "123.123.123.123", "port": 8888,
            "area": "香港", "startTime": "2026-01-01 15:12:01",
            "endTime": "2026-04-01 15:12:01", "renewPrice": 30,
            "paymentCycle": 1,
        }
        a = Accelerator._from_dict(data)
        assert a.id == 1
        assert a.ip == "123.123.123.123"
        assert a.port == 8888
        assert a.area == "香港"

    def test_order_request_to_dict(self):
        req = AcceleratorOrderRequest(productId=1, region="cn-sh2",
                                      ip="1.2.3.4", port=8080,
                                      area="Hong Kong", paymentCycle=1)
        d = req.to_dict()
        assert d["productId"] == 1
        assert d["ip"] == "1.2.3.4"

    def test_modify_request_to_dict(self):
        req = AcceleratorModifyRequest(ip="2.3.4.5", area="Tokyo")
        assert req.to_dict() == {"ip": "2.3.4.5", "area": "Tokyo"}

    def test_port_request_to_dict(self):
        req = AcceleratorPortRequest(port=443)
        assert req.to_dict() == {"port": 443}


class TestTrafficUsage:
    def test_from_dict(self):
        data = {"Date": 1782921600, "Traffic": 66, "BillingState": "No"}
        t = TrafficUsage._from_dict(data)
        assert t.Date == 1782921600
        assert t.Traffic == 66.0
        assert t.BillingState == "No"

    def test_from_dict_billing_yes(self):
        data = {"Date": 1783008000, "Traffic": 63, "BillingState": "Yes"}
        t = TrafficUsage._from_dict(data)
        assert t.BillingState == "Yes"

    def test_from_dict_traffic_float(self):
        data = {"Date": 1783094400, "Traffic": "58.5", "BillingState": "No"}
        t = TrafficUsage._from_dict(data)
        assert t.Traffic == 58.5

    def test_from_list(self):
        data = [
            {"Date": 1782921600, "Traffic": 66, "BillingState": "No"},
            {"Date": 1783008000, "Traffic": 63, "BillingState": "Yes"},
        ]
        records = TrafficUsage._from_list(data)
        assert len(records) == 2
        assert records[0].Date == 1782921600
        assert records[1].BillingState == "Yes"

    def test_from_list_empty(self):
        records = TrafficUsage._from_list([])
        assert records == []


class TestBalance:
    def test_from_dict(self):
        data = {"balance": 1000}
        b = Balance._from_dict(data)
        assert b.balance == 1000.0

    def test_from_dict_float(self):
        data = {"balance": 99.99}
        b = Balance._from_dict(data)
        assert b.balance == 99.99


class TestFromDict:
    def test_ignores_unknown_fields(self):
        data = {"id": 1, "city": "Tokyo", "extra_field": "should be ignored"}
        r = Region._from_dict(data)
        assert r.id == 1
        assert r.city == "Tokyo"

    def test_str_to_float_conversion(self):
        p = CloudProduct._from_dict({"id": 1, "priceHour": "0.058"})
        assert isinstance(p.priceHour, float)
        assert p.priceHour == 0.058
