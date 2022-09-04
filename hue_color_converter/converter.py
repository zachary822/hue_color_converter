from typing import NamedTuple, NewType, Union

from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points

from hue_color_converter.gamuts import DEFAULT_GAMUT, get_gamut


class RGB(NamedTuple):
    r: float
    g: float
    b: float


class XYZ(NamedTuple):
    x: float
    y: float
    z: float


class XY(NamedTuple):
    x: float
    y: float


Brightness = NewType("Brightness", float)


class Converter:
    gamut: Polygon

    def __init__(self, gamut: Union[str, list[tuple[float, float]], Polygon, None] = None):
        if isinstance(gamut, str):
            self.gamut = get_gamut(gamut)
        elif isinstance(gamut, list):
            self.gamut = Polygon(gamut)
        elif gamut is None:
            self.gamut = DEFAULT_GAMUT
        else:
            self.gamut = gamut

    @staticmethod
    def hex_to_rgb(hex_color: str) -> RGB:
        b = bytes.fromhex(hex_color)
        if len(b) != 3:
            raise ValueError("should be rgb hex code")
        return RGB._make(c / 255 for c in b)

    @staticmethod
    def gamma_correction(c: float) -> float:
        return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92

    @staticmethod
    def reverse_gamma_correction(c: float) -> float:
        return min(
            max(0.0, 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1.0 / 2.4) - 0.055),
            1.0,
        )

    @classmethod
    def rgb_gamma_correction(cls, rgb: RGB) -> RGB:
        return RGB._make(map(cls.gamma_correction, rgb))

    @staticmethod
    def rgb_to_xyz(rgb: RGB) -> XYZ:
        r, g, b = rgb

        x = r * 0.4124 + g * 0.3576 + b * 0.1805
        y = r * 0.2126 + g * 0.7152 + b * 0.0722
        z = r * 0.0193 + g * 0.1192 + b * 0.9505

        return XYZ(x, y, z)

    @staticmethod
    def _xyz_to_xyb(xyz: XYZ) -> tuple[XY, Brightness]:
        """
        raw xy and brightness
        """
        x, y, _ = xyz
        s = sum(xyz)

        return XY(x / s, y / s), Brightness(y)

    def xyz_to_xyb(self, xyz: XYZ):
        """
        Corrected xy and brightness
        """

        xy, b = self._xyz_to_xyb(xyz)
        _xy = Point(xy)

        if self.gamut.contains(_xy):
            return xy, b
        nearest = nearest_points(self.gamut, _xy)[0]
        return XY(nearest.x, nearest.y), b

    def rgb_to_xyb(self, rgb: RGB) -> tuple[XY, Brightness]:
        return self.xyz_to_xyb(self.rgb_to_xyz(self.rgb_gamma_correction(rgb)))

    def hex_to_xyb(self, hex_color: str) -> tuple[XY, Brightness]:
        return self.rgb_to_xyb(self.hex_to_rgb(hex_color))

    @staticmethod
    def xyb_to_xyz(x: float, y: float, b: float = 1) -> XYZ:
        if b > 1:
            b /= 100
        z = 1 - x - y

        return XYZ(b / y * x, b, b / y * z)

    @staticmethod
    def xyz_to_rgb(xyz: XYZ) -> RGB:
        x, y, z = xyz

        r = x * 3.2406255 - y * 1.5372080 - z * 0.4986268
        g = -x * 0.9689307 + y * 1.8757561 + z * 0.0415175
        b = x * 0.0557101 - y * 0.2040211 + z * 1.0569959

        return RGB(r, g, b)

    @classmethod
    def rgb_reverse_gamma_correction(cls, rgb: RGB) -> RGB:
        return RGB._make(map(cls.reverse_gamma_correction, rgb))

    @classmethod
    def xyb_to_rgb(cls, x: float, y: float, brightness: float = 1) -> RGB:
        return cls.rgb_reverse_gamma_correction(cls.xyz_to_rgb(cls.xyb_to_xyz(x, y, brightness)))

    @classmethod
    def xyb_to_hex(cls, x: float, y: float, brightness: float = 1) -> str:
        return bytes(round(c * 255) for c in cls.xyb_to_rgb(x, y, brightness)).hex()
