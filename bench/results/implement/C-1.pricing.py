"""Cart pricing in integer cents."""

SUPPORTED_REGIONS = ("US", "EU", "UK")
SHIPPING_FEE = {"US": 599, "EU": 899, "UK": 899}
TAX_RATE_PERCENT = {"US": 7, "EU": 20, "UK": 20}
FREE_SHIPPING_THRESHOLD = 5000
GIFT_CARD_CATEGORY = "gift-card"
SAVE10_PERCENT = 10
FLAT500_AMOUNT = 500
FLAT500_MIN_ELIGIBLE = 3000
MEMBER_PERCENT = 5


def _pct_half_up(amount, percent):
    """Return amount * percent / 100 rounded half up, using integer math only."""
    return (amount * percent + 50) // 100


def quote(cart, region, coupon=None, member=False):
    if region not in SUPPORTED_REGIONS:
        raise ValueError("unsupported region")
    for item in cart:
        if item["qty"] < 1:
            raise ValueError("invalid qty")

    if not cart:
        return {"subtotal": 0, "discount": 0, "shipping": 0, "tax": 0, "total": 0}

    subtotal = sum(item["price"] * item["qty"] for item in cart)
    eligible = sum(
        item["price"] * item["qty"]
        for item in cart
        if item["category"] != GIFT_CARD_CATEGORY
    )

    if coupon is None:
        coupon_discount = 0
    else:
        code = coupon.strip().upper()
        if code == "SAVE10":
            coupon_discount = _pct_half_up(eligible, SAVE10_PERCENT)
        elif code == "FLAT500":
            coupon_discount = FLAT500_AMOUNT if eligible >= FLAT500_MIN_ELIGIBLE else 0
        else:
            raise ValueError("unknown coupon")

    if member:
        member_discount = _pct_half_up(eligible - coupon_discount, MEMBER_PERCENT)
    else:
        member_discount = 0
    discount = coupon_discount + member_discount

    if member or subtotal - discount >= FREE_SHIPPING_THRESHOLD:
        shipping = 0
    else:
        shipping = SHIPPING_FEE[region]

    tax = _pct_half_up(eligible - discount + shipping, TAX_RATE_PERCENT[region])
    total = subtotal - discount + shipping + tax

    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
