"""Shopping cart pricing. All money is integer cents."""

REGIONS = {"US", "EU", "UK"}
SHIPPING_RATES = {"US": 599, "EU": 899, "UK": 899}
TAX_RATES = {"US": 7, "EU": 20, "UK": 20}  # whole percent
FREE_SHIPPING_THRESHOLD = 5000
FLAT500_MIN_ELIGIBLE = 3000
FLAT500_AMOUNT = 500
SAVE10_PERCENT = 10
MEMBER_PERCENT = 5
GIFT_CARD = "gift-card"


def _pct_half_up(amount: int, percent: int) -> int:
    """Return amount * percent / 100 rounded half up. Inputs must be non-negative ints."""
    return (amount * percent + 50) // 100


def quote(cart, region, coupon=None, member=False) -> dict:
    if region not in REGIONS:
        raise ValueError("unsupported region")
    if any(item["qty"] < 1 for item in cart):
        raise ValueError("invalid qty")
    if not cart:
        return {"subtotal": 0, "discount": 0, "shipping": 0, "tax": 0, "total": 0}

    subtotal = 0
    eligible = 0
    for item in cart:
        line = item["price"] * item["qty"]
        subtotal += line
        if item["category"] != GIFT_CARD:
            eligible += line

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
        shipping = SHIPPING_RATES[region]

    tax = _pct_half_up(eligible - discount + shipping, TAX_RATES[region])
    total = subtotal - discount + shipping + tax

    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
