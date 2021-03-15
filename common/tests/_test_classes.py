from common.user import APRInfo
from common.util import PaidRemain


def test_PaidRemain_addition():
    a = PaidRemain(paid=10, remain=100)
    b = PaidRemain(paid=20, remain=50)
    c = a + b
    # verify new ones is added correctly
    assert c.remain == 150 and c.paid == 30
    # old ones are not changed
    assert a.paid == 10 and b.paid == 20
    assert a.remain == 100 and b.remain == 50


def test_PaidRemain_equals():
    a = PaidRemain(paid=10, remain=100)
    b = PaidRemain(paid=20, remain=50)
    assert a == a and a != b


def test_APRInfo_addition():
    a = PaidRemain(paid=10, remain=100)
    b = PaidRemain(paid=20, remain=50)
    aa = PaidRemain(paid=100, remain=1000)

    apr1 = APRInfo(apr=0.1, principal=a, interest=aa)
    apr2 = APRInfo(apr=0.4, principal=b)

    apr3 = apr1 + apr2

    # verify it is summed correctly
    assert apr3.principal.paid == a.paid + b.paid
    assert apr3.principal.remain == a.remain + b.remain
    assert apr3.interest.paid == aa.paid and apr3.interest.remain == aa.remain
    assert apr1.principal.paid == 10 and apr1.principal.remain == 100

    # apr should be weighted sum
    weighted_average = ((0.4 * 50) + (0.1 * 100)) / 150
    assert apr3.apr == weighted_average

    # verify equals operator works too
    assert apr1 != apr2 and apr3 == apr3
