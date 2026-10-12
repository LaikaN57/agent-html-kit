"""Cart pricing: subtotal, discounts, shipping, tax and total in integer cents."""

SHIPPING_RATES = {"US": 599, "EU": 899, "UK": 899}
TAX_PERCENT = {"US": 7, "EU": 20, "UK": 20}

FREE_SHIPPING_THRESHOLD = 5000
FLAT500_MINIMUM = 3000
FLAT500_AMOUNT = 500
SAVE10_PERCENT = 10
MEMBER_PERCENT = 5
GIFT_CARD = "gift-card"

_KNOWN_COUPONS = {"SAVE10", "FLAT500"}


def _pct(amount, percent):
    """Return percent% of a non-negative integer amount, rounded half up."""
    return (amount * percent + 50) // 100


def quote(cart, region, coupon=None, member=False):
    if region not in TAX_PERCENT:
        raise ValueError("unsupported region")

    for item in cart:
        if item["qty"] < 1:
            raise ValueError("invalid qty")

    if coupon is None:
        code = None
    else:
        code = coupon.strip().upper()
        if code not in _KNOWN_COUPONS:
            raise ValueError("unknown coupon")

    if not cart:
        return {"subtotal": 0, "discount": 0, "shipping": 0, "tax": 0, "total": 0}

    subtotal = 0
    eligible = 0
    for item in cart:
        line = item["price"] * item["qty"]
        subtotal += line
        if item["category"] != GIFT_CARD:
            eligible += line

    if code == "SAVE10":
        coupon_discount = _pct(eligible, SAVE10_PERCENT)
    elif code == "FLAT500" and eligible >= FLAT500_MINIMUM:
        coupon_discount = FLAT500_AMOUNT
    else:
        coupon_discount = 0

    member_discount = _pct(eligible - coupon_discount, MEMBER_PERCENT) if member else 0
    discount = coupon_discount + member_discount

    if member or subtotal - discount >= FREE_SHIPPING_THRESHOLD:
        shipping = 0
    else:
        shipping = SHIPPING_RATES[region]

    tax = _pct(eligible - discount + shipping, TAX_PERCENT[region])
    total = subtotal - discount + shipping + tax

    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
