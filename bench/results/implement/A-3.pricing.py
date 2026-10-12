"""Price quotes for shopping carts. All money values are integer cents."""

REGIONS = {"US", "EU", "UK"}
SHIPPING = {"US": 599, "EU": 899, "UK": 899}
TAX_PCT = {"US": 7, "EU": 20, "UK": 20}
FREE_SHIPPING_THRESHOLD = 5000
FLAT500_MIN = 3000
GIFT_CARD = "gift-card"


def _pct_half_up(amount: int, pct: int) -> int:
    return (amount * pct + 50) // 100


def quote(cart, region, coupon=None, member=False) -> dict:
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
        coupon_discount = 0
    else:
        code = coupon.strip().upper()
        if code == "SAVE10":
            coupon_discount = _pct_half_up(eligible, 10)
        elif code == "FLAT500":
            coupon_discount = 500 if eligible >= FLAT500_MIN else 0
        else:
            raise ValueError("unknown coupon")

    member_discount = _pct_half_up(eligible - coupon_discount, 5) if member else 0
    discount = coupon_discount + member_discount

    if member or subtotal - discount >= FREE_SHIPPING_THRESHOLD:
        shipping = 0
    else:
        shipping = SHIPPING[region]

    tax = _pct_half_up(eligible - discount + shipping, TAX_PCT[region])
    total = subtotal - discount + shipping + tax

    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
