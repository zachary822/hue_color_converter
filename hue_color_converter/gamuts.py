from shapely.geometry import Polygon

GAMUT_A = Polygon([(0.704, 0.296), (0.2151, 0.7106), (0.138, 0.08)])

GAMUT_B = Polygon([(0.675, 0.322), (0.409, 0.518), (0.167, 0.04)])

GAMUT_C = Polygon([(0.6915, 0.3038), (0.17, 0.7), (0.1532, 0.0475)])

DEFAULT_GAMUT = Polygon([(1, 0), (0, 1), (0, 0)])


def get_gamut(model_id: str) -> Polygon:
    if model_id in {
        "LST001",
        "LLC005",
        "LLC006",
        "LLC007",
        "LLC010",
        "LLC011",
        "LLC012",
        "LLC013",
        "LLC014",
        "A",
    }:
        return GAMUT_A
    if model_id in {"LCT001", "LCT007", "LCT002", "LCT003", "LLM001", "B"}:
        return GAMUT_B
    if model_id in {
        "LCT010",
        "LCT011",
        "LCT012",
        "LCT014",
        "LCT015",
        "LCT016",
        "LLC020",
        "LST002",
        "C",
    }:
        return GAMUT_C

    return DEFAULT_GAMUT
