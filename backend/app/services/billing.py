def estimate_bill(
    total_kwh: float
) -> float:

    slabs = [
        (100, 3.5),
        (200, 4.5),
        (300, 6.0),
        (float("inf"), 7.5)
    ]

    remaining = total_kwh
    prev_limit = 0
    bill = 0.0

    for limit, rate in slabs:

        units_in_slab = min(
            remaining,
            limit - prev_limit
        )

        if units_in_slab <= 0:
            break

        bill += (
            units_in_slab * rate
        )

        remaining -= units_in_slab
        prev_limit = limit

    return round(bill, 2)