def percent(part, total):
    """Доля в процентах без деления на ноль."""
    if not total:
        return 0
    return round(part * 100 / total)