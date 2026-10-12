"""Cart pricing in integer cents."""

__all__ = ["quote"]

REGIONS = {"US", "EU", "UK"}
SHIPPING = {"US": 599, "EU": 899, "UK": 899}
TAX_PCT = {"US": 7, "EU": 20, "UK": 20}
FREE_SHIPPING_MIN = 5000
FLAT500_MIN = 3000
GIFT_CARD = "gift-card"


def _half_up_pct(amount, pct):
    """Return pct% of amount (non-negative int cents), rounded half up."""
    return (amount * pct + 50) // 100


def quote(cart, region, coupon=None, member=False):
    if region not in REGIONS:
        raise ValueError("unsupported region")
    for item in cart:
        if item["qty"] < 1:
            raise ValueError("invalid qty")
    code = None if coupon is None else coupon.strip().upper()
    if code not in (None, "SAVE10", "FLAT500"):
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
        coupon_discount = _half_up_pct(eligible, 10)
    elif code == "FLAT500":
        coupon_discount = 500 if eligible >= FLAT500_MIN else 0
    else:
        coupon_discount = 0

    member_discount = _half_up_pct(eligible - coupon_discount, 5) if member else 0
    discount = coupon_discount + member_discount

    if member or subtotal - discount >= FREE_SHIPPING_MIN:
        shipping = 0
    else:
        shipping = SHIPPING[region]

    tax = _half_up_pct(eligible - discount + shipping, TAX_PCT[region])
    total = subtotal - discount + shipping + tax

    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
