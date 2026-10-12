"""Shopping cart pricing. All money is integer cents."""

REGIONS = {"US", "EU", "UK"}
TAX_PERCENT = {"US": 7, "EU": 20, "UK": 20}
SHIPPING_FEE = {"US": 599, "EU": 899, "UK": 899}
FREE_SHIPPING_THRESHOLD = 5000
FLAT500_MINIMUM = 3000
GIFT_CARD = "gift-card"


def _half_up_pct(amount, percent):
    """Return percent% of amount in cents, rounded half up (integers only)."""
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

    coupon_discount = 0
    if coupon is not None:
        code = coupon.strip().upper()
        if code == "SAVE10":
            coupon_discount = _half_up_pct(eligible, 10)
        elif code == "FLAT500":
            coupon_discount = 500 if eligible >= FLAT500_MINIMUM else 0
        else:
            raise ValueError("unknown coupon")

    member_discount = _half_up_pct(eligible - coupon_discount, 5) if member else 0
    discount = coupon_discount + member_discount

    if member or subtotal - discount >= FREE_SHIPPING_THRESHOLD:
        shipping = 0
    else:
        shipping = SHIPPING_FEE[region]

    tax = _half_up_pct(eligible - discount + shipping, TAX_PERCENT[region])
    total = subtotal - discount + shipping + tax

    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
