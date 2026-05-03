def calc_stat(base: int, iv: int, ev: int, *, is_hp: bool = False) -> int:
    """Level-50 stat formula (Gen I-style)."""
    inner = (2 * base + iv + ev // 4) * 50 // 100
    return inner + 60 if is_hp else inner + 5
