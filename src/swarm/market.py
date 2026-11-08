"""Food-for-coins call auction shared by the private-property islands (E08, E12)."""

from __future__ import annotations

from swarm.economy import _num


def _market(isl, orders: dict, day: int) -> int:
    """Food-for-coins call auction, one unit at a time at the bid/ask midpoint."""
    bids = sorted([[p, _num(o.get("max_price")), _num(o.get("buy_food"), hi=10)] for p, o in orders.items()
                   if _num(o.get("buy_food"), hi=10) >= 1], key=lambda b: -b[1])
    asks = sorted([[p, _num(o.get("min_price")), min(_num(o.get("sell_food"), hi=10), p.inv.get("food", 0))]
                   for p, o in orders.items()], key=lambda a: a[1])
    vol = 0
    for b in bids:
        for a in asks:
            while b[2] >= 1 and a[2] >= 1 and a[0] is not b[0] and b[1] >= a[1]:
                price = (b[1] + a[1]) / 2
                if b[0].coins < price or a[0].inv.get("food", 0) < 1 or not (a[0].alive and b[0].alive):
                    break
                b[0].coins -= price; a[0].coins += price
                a[0].inv["food"] -= 1; b[0].inv["food"] = b[0].inv.get("food", 0) + 1
                b[2] -= 1; a[2] -= 1; vol += 1
                isl.emit(day, "trade", buyer=b[0].name, seller=a[0].name, price=price)
    return vol
