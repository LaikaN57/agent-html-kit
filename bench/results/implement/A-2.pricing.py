"""Shopping cart pricing. All money values are integer cents."""

SHIPPING = {"US": 599, "EU": 899, "UK": 899}
TAX_PCT = {"US": 7, "EU": 20, "UK": 20}
FREE_SHIPPING_THRESHOLD = 5000
FLAT500_MIN = 3000
FLAT500_AMOUNT = 500
SAVE10_PCT = 10
MEMBER_PCT = 5
GIFT_CARD = "gift-card"


def _pct_half_up(amount: int, pct: int) -> int:
    """Return amount * pct / 100, rounded half up to a whole cent (amount >= 0)."""
    return (amount * pct + 50) // 100


def quote(cart, region, coupon=None, member=False) -> dict:
    if region not in SHIPPING:
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
            coupon_discount = _pct_half_up(eligible, SAVE10_PCT)
        elif code == "FLAT500":
            coupon_discount = FLAT500_AMOUNT if eligible >= FLAT500_MIN else 0
        else:
            raise ValueError("unknown coupon")

    if member:
        member_discount = _pct_half_up(eligible - coupon_discount, MEMBER_PCT)
    else:
        member_discount = 0
    discount = coupon_discount + member_discount

    if member or subtotal - discount >= FREE_SHIPPING_THRESHOLD:
        shipping = 0
    else:
        shipping = SHIPPING[region]

    tax = _pct_half_up(eligible - discount + shipping, TAX_PCT[region])
    total = subtotal - discount + shipping + tax

    return {
        "subtotal": int(subtotal),
        "discount": int(discount),
        "shipping": int(shipping),
        "tax": int(tax),
        "total": int(total),
    }
