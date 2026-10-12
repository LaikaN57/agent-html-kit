"""Price a shopping cart. All money is integer cents."""

TAX_PERCENT = {"US": 7, "EU": 20, "UK": 20}
SHIPPING = {"US": 599, "EU": 899, "UK": 899}
FREE_SHIPPING_THRESHOLD = 5000
FLAT500_MINIMUM = 3000
FLAT500_AMOUNT = 500
SAVE10_PERCENT = 10
MEMBER_PERCENT = 5
GIFT_CARD = "gift-card"

# Open question Q1: an empty cart returns zeros before the coupon is parsed,
# so an unknown coupon on an empty cart is not an error. Set to False to
# validate the coupon even when the cart is empty.
EMPTY_CART_SKIPS_COUPON_CHECK = True


def _pct_half_up(amount, percent):
    """Return amount * percent / 100 rounded half up (amount >= 0)."""
    return (amount * percent + 50) // 100


def _coupon_discount(coupon, eligible):
    if coupon is None:
        return 0
    code = coupon.strip().upper()
    if code == "SAVE10":
        return _pct_half_up(eligible, SAVE10_PERCENT)
    if code == "FLAT500":
        return FLAT500_AMOUNT if eligible >= FLAT500_MINIMUM else 0
    raise ValueError("unknown coupon")


def quote(cart, region, coupon=None, member=False):
    if region not in TAX_PERCENT:
        raise ValueError("unsupported region")
    for item in cart:
        if item["qty"] < 1:
            raise ValueError("invalid qty")

    if not cart:
        if not EMPTY_CART_SKIPS_COUPON_CHECK:
            _coupon_discount(coupon, 0)
        return {"subtotal": 0, "discount": 0, "shipping": 0, "tax": 0, "total": 0}

    subtotal = 0
    eligible = 0
    for item in cart:
        line = item["price"] * item["qty"]
        subtotal += line
        if item["category"] != GIFT_CARD:
            eligible += line

    c = _coupon_discount(coupon, eligible)
    m = _pct_half_up(eligible - c, MEMBER_PERCENT) if member else 0
    discount = c + m

    if member or subtotal - discount >= FREE_SHIPPING_THRESHOLD:
        shipping = 0
    else:
        shipping = SHIPPING[region]

    tax = _pct_half_up(eligible - discount + shipping, TAX_PERCENT[region])
    total = subtotal - discount + shipping + tax

    return {
        "subtotal": subtotal,
        "discount": discount,
        "shipping": shipping,
        "tax": tax,
        "total": total,
    }
