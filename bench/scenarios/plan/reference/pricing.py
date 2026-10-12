"""Reference implementation used only to validate hidden_test.py."""
from decimal import Decimal, ROUND_HALF_UP

SHIPPING = {"US": 599, "EU": 899, "UK": 899}
TAX = {"US": Decimal("0.07"), "EU": Decimal("0.20"), "UK": Decimal("0.20")}


def _half_up(x):
    return int(Decimal(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def quote(cart, region, coupon=None, member=False):
    if region not in SHIPPING:
        raise ValueError("unsupported region")
    if any(it["qty"] < 1 for it in cart):
        raise ValueError("invalid qty")
    if not cart:
        return {"subtotal": 0, "discount": 0, "shipping": 0, "tax": 0, "total": 0}
    subtotal = sum(it["price"] * it["qty"] for it in cart)
    eligible = sum(it["price"] * it["qty"] for it in cart if it["category"] != "gift-card")
    discount = 0
    if coupon is not None:
        code = coupon.strip().upper()
        if code == "SAVE10":
            discount = _half_up(Decimal(eligible) * Decimal("0.10"))
        elif code == "FLAT500":
            discount = 500 if eligible >= 3000 else 0
        else:
            raise ValueError("unknown coupon")
    if member:
        discount += _half_up(Decimal(eligible - discount) * Decimal("0.05"))
    shipping = 0 if member or subtotal - discount >= 5000 else SHIPPING[region]
    tax = _half_up(Decimal(eligible - discount + shipping) * TAX[region])
    total = subtotal - discount + shipping + tax
    return {"subtotal": subtotal, "discount": discount, "shipping": shipping, "tax": tax, "total": total}
