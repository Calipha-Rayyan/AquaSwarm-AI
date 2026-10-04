def verify_quantity(expected, actual, tolerance_percent=10):
    expected = float(expected)
    actual = float(actual)

    tolerance = expected * (
        tolerance_percent / 100
    )

    difference = abs(
        expected - actual
    )

    passed = difference <= tolerance

    return {
        "expected": expected,
        "actual": actual,
        "difference": round(difference, 2),
        "tolerance": round(tolerance, 2),
        "status": "PASSED" if passed else "EXCEPTION",
        "requires_replan": not passed
    }