"""Cart pricing. All money values are integer cents."""

REGIONS = {"US", "EU", "UK"}
SHIPPING_FEE = {"US": 599, "EU": 899, "UK": 899}
TAX_RATE = {"US": 7, "EU": 20, "UK": 20}
FREE_SHIPPING_THRESHOLD = 5000
FLAT500_MIN = 3000
GIFT_CARD = "gift-card"


def _pct(amount, rate):
    """Return rate% of amount, rounded half up to a whole cent (amount >= 0)."""
    return (amount * rate + 50) // 100


def quote(cart, region, coupon=None, member=False):
    if region not in REGIONS:
        raise ValueError("unsupported region")
    if any(item["qty"] < 1 for item in cart):
        raise ValueError("invalid qty")

    if not cart:
        return {"subtotal": 0, "discount": 0, "shipping": 0, "tax": 0, "total": 0}

    subtotal = sum(item["price"] * item["qty"] for item in cart)
    eligible = sum(
        item["price"] * item["qty"] for item in cart if item["category"] != GIFT_CARD
    )

    if coupon is None:
        coupon_discount = 0
    else:
        code = coupon.strip().upper()
        if code == "SAVE10":
            coupon_discount = _pct(eligible, 10)
        elif code == "FLAT500":
            coupon_discount = 500 if eligible >= FLAT500_MIN else 0
        else:
            raise ValueError("unknown coupon")

    member_discount = _pct(eligible - coupon_discount, 5) if member else 0
    discount = coupon_discount + member_discount

    if member or subtotal - discount >= FREE_SHIPPING_THRESHOLD:
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
