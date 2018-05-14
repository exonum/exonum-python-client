import exonum.datatypes as exonum
import exonum.transactions as tx

import decimal
from datetime import datetime


transactions = tx.transactions(service_id=250)

class Policy(metaclass=exonum.EncodingStruct):
    policy_type = exonum.Str
    unique_id = exonum.Str
    insured_name = exonum.Str
    insured_state = exonum.Str
    zip_code = exonum.Str
    industry_sector = exonum.Str
    annual_revenue = exonum.Str
    total_lives = exonum.u16
    inception = exonum.DateTime
    expiry = exonum.DateTime
    limit = exonum.u16
    excess = exonum.u16
    currency = exonum.Str
    gross_premium_no_ipt = exonum.u16
    tax = exonum.Decimal
    tax_ammount = exonum.u16
    risk_management_fee = exonum.u16
    commision = exonum.u16
    net_premium_due = exonum.u16


@transactions
class CreatePolicy(metaclass=exonum.EncodingStruct):
    content = Policy
    public_key = exonum.PublicKey


pkey = bytes.fromhex(
    "692e5734b12d3446def47954c9d4d4ffcf6494d621e2a117e77c6ba07b093038")

def test_tx_serialize():
    p = Policy(
        policy_type = "New",
        unique_id = "uniq_id",
        insured_name = "name",
        insured_state = "state",
        zip_code = "zip",
        industry_sector = "sector",
        annual_revenue = "revenue",
        total_lives = 1,
        inception = datetime(2014, 7, 8, 9, 10, 11),
        expiry = datetime(2014, 7, 8, 9, 10, 11),
        limit = 2,
        excess = 3,
        currency = "usd",
        gross_premium_no_ipt = 4,
        tax = decimal.Decimal("123.456789"),
        tax_ammount = 5,
        risk_management_fee = 6,
        commision = 7,
        net_premium_due = 8)

    tx = CreatePolicy(
        content = p,
        public_key = pkey)

    with open("./tests/test_data/bin2.bin", "rb") as f:
        data = f.read()
    print("rs " + data[:-64].hex())
    data = tx.to_bytes()
    print("py " + data.hex())

    # assert tx == CreatePolicy.read_buffer(data)


def test_tx_deserialize():
    with open("./tests/test_data/bin2.bin", "rb") as f:
        data = f.read()

    cnt = len(data) - 64

    p = CreatePolicy.read_buffer(data, cnt=cnt)

    assert p.content.total_lives.val == 1
    assert p.content.tax.val == decimal.Decimal("123.456789")
    assert p.content.policy_type.val == "New"
    assert p.service_id == 250
