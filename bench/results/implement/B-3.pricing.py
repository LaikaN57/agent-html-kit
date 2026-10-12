"""Price quotes for a shopping cart. All amounts are integer cents."""

# Region data: shipping fee (cents) and tax percent.
REGIONS = {
    "US": {"shipping": 599, "tax_percent": 7},
    "EU": {"shipping": 899, "tax_percent": 20},
    "UK": {"shipping": 899, "tax_percent": 20},
}

FREE_SHIPPING_THRESHOLD = 5000
FLAT500_AMOUNT = 500
FLAT500_MIN_ELIGIBLE = 3000
SAVE10_PERCENT = 10
MEMBER_PERCENT = 5
GIFT_CARD_CATEGORY = "gift-card"


def _pct_half_up(amount, percent):
    """Return amount * percent / 100 rounded half up, for amount >= 0."""
    return (amount * percent + 50) // 100


def quote(cart, region, coupon=None, member=False):
    if region not in REGIONS:
        raise ValueError("unsupported region")
    for item in cart:
        if item["qty"] < 1:
            raise ValueError("invalid qty")
    if not cart:
        return {"subtotal": 0, "discount": 0, "shipping": 0, "tax": 0, "total": 0}

    subtotal = 0
    eligible = 0
    for item in cart:
        line = item["price"] * item["qty"]
        subtotal += line
        if item["category"] != GIFT_CARD_CATEGORY:
            eligible += line

    if coupon is None:
        coupon_disc = 0
    else:
        code = coupon.strip().upper()
        if code == "SAVE10":
            coupon_disc = _pct_half_up(eligible, SAVE10_PERCENT)
        elif code == "FLAT500":
            coupon_disc = FLAT500_AMOUNT if eligible >= FLAT500_MIN_ELIGIBLE else 0
        else:
            raise ValueError("unknown coupon")

    member_disc = _pct_half_up(eligible - coupon_disc, MEMBER_PERCENT) if member else 0
    discount = coupon_disc + member_disc

    if member or subtotal - discount >= FREE_SHIPPING_THRESHOLD:
        shipping = 0
    else:
        shipping = REGIONS[region]["shipping"]

    tax = _pct_half_up(eligible - discount + shipping, REGIONS[region]["tax_percent"])
    total = subtotal - discount + shipping + tax

    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
