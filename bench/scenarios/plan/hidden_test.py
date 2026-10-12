"""Hidden acceptance tests for the plan scenario. The implementing agent never sees this file.

Usage: python hidden_test.py <dir containing pricing.py>
Prints a JSON line {"passed": n, "total": m, "failed": [...]}.
"""
import importlib.util
import json
import sys
from pathlib import Path


def load(dir_):
    spec = importlib.util.spec_from_file_location("pricing", Path(dir_) / "pricing.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.quote


def item(price, qty=1, category="general", sku="SKU"):
    return {"sku": sku, "price": price, "qty": qty, "category": category}


def raises(fn, msg):
    try:
        fn()
    except ValueError as e:
        return str(e) == msg
    except Exception:
        return False
    return False


def cases(quote):
    Z = {"subtotal": 0, "discount": 0, "shipping": 0, "tax": 0, "total": 0}
    q = lambda *a, **k: quote(*a, **k)
    return {
        "empty_cart_zeros": lambda: q([], "US") == Z,
        "bad_region_first": lambda: raises(lambda: q([], "CA"), "unsupported region"),
        "bad_region_before_qty": lambda: raises(lambda: q([item(100, 0)], "CA"), "unsupported region"),
        "invalid_qty": lambda: raises(lambda: q([item(100, 0)], "US"), "invalid qty"),
        "unknown_coupon": lambda: raises(lambda: q([item(1000)], "US", "SAVE20"), "unknown coupon"),
        "simple_us": lambda: q([item(2000)], "US") == {"subtotal": 2000, "discount": 0, "shipping": 599, "tax": 182, "total": 2781},
        "qty_multiplies": lambda: q([item(1250, 3)], "EU")["subtotal"] == 3750,
        "save10_eu": lambda: q([item(3333)], "EU", "SAVE10") == {"subtotal": 3333, "discount": 333, "shipping": 899, "tax": 780, "total": 4679},
        "coupon_case_whitespace": lambda: q([item(3333)], "EU", "  save10 ")["discount"] == 333,
        "flat500_below_threshold": lambda: q([item(2999)], "US", "FLAT500")["discount"] == 0,
        "flat500_at_threshold": lambda: q([item(3000)], "US", "FLAT500")["discount"] == 500,
        "flat500_ignores_gift_cards": lambda: q([item(5000, category="gift-card"), item(1000)], "US", "FLAT500")["discount"] == 0,
        "gift_card_untaxed": lambda: q([item(2500, category="gift-card")], "US") == {"subtotal": 2500, "discount": 0, "shipping": 599, "tax": 42, "total": 3141},
        "member_after_coupon": lambda: q([item(4000)], "US", "SAVE10", member=True) == {"subtotal": 4000, "discount": 580, "shipping": 0, "tax": 239, "total": 3659},
        "free_ship_at_5000": lambda: q([item(5000)], "US")["shipping"] == 0,
        "paid_ship_at_4999": lambda: q([item(4999)], "US")["shipping"] == 599,
        "free_ship_uses_net": lambda: q([item(5500)], "UK", "SAVE10") == {"subtotal": 5500, "discount": 550, "shipping": 899, "tax": 1170, "total": 7019},
        "half_up_rounding": lambda: q([item(158)], "US", member=True) == {"subtotal": 158, "discount": 8, "shipping": 0, "tax": 11, "total": 161},
        "returns_ints": lambda: all(type(v) is int for v in q([item(3333)], "EU", "SAVE10", member=True).values()),
    }


def main():
    try:
        quote = load(sys.argv[1])
    except Exception as e:  # missing or broken module
        print(json.dumps({"passed": 0, "total": 19, "failed": ["import: " + repr(e)]}))
        return
    results = {}
    for name, fn in cases(quote).items():
        try:
            results[name] = bool(fn())
        except Exception:
            results[name] = False
    failed = [k for k, v in results.items() if not v]
    print(json.dumps({"passed": len(results) - len(failed), "total": len(results), "failed": failed}))


if __name__ == "__main__":
    main()
