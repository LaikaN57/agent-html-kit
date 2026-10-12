"""Cart pricing: quote() returns subtotal, discount, shipping, tax and total in integer cents."""

REGIONS = {"US", "EU", "UK"}
TAX_RATE = {"US": 7, "EU": 20, "UK": 20}
SHIPPING_FEE = {"US": 599, "EU": 899, "UK": 899}
FREE_SHIPPING_THRESHOLD = 5000
FLAT500_MIN = 3000
GIFT_CARD = "gift-card"


def _pct(amount, percent):
    """Percentage of a non-negative cent amount, rounded half up, integer-only."""
    return (amount * percent + 50) // 100


def quote(cart, region, coupon=None, member=False):
    if region not in REGIONS:
        raise ValueError("unsupported region")
    for item in cart:
        if item["qty"] < 1:
            raise ValueError("invalid qty")

    if not cart:
        return {"subtotal": 0, "discount": 0, "shipping": 0, "tax": 0, "total": 0}

    subtotal = sum(item["price"] * item["qty"] for item in cart)
    eligible = sum(
        item["price"] * item["qty"] for item in cart if item["category"] != GIFT_CARD
    )

    if coupon is None:
        coupon_disc = 0
    else:
        code = coupon.strip().upper()
        if code == "SAVE10":
            coupon_disc = _pct(eligible, 10)
        elif code == "FLAT500":
            coupon_disc = 500 if eligible >= FLAT500_MIN else 0
        else:
            raise ValueError("unknown coupon")

    member_disc = _pct(eligible - coupon_disc, 5) if member else 0
    discount = coupon_disc + member_disc

    if member:
        shipping = 0
    elif subtotal - discount >= FREE_SHIPPING_THRESHOLD:
        shipping = 0
    else:
        shipping = SHIPPING_FEE[region]

    tax = _pct(eligible - discount + shipping, TAX_RATE[region])
    total = subtotal - discount + shipping + tax

    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
