from collections.abc import Sequence
from typing import NamedTuple, NewType, Optional, Union

import numpy as np
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


class XYB(NamedTuple):
    xy: np.ndarray
    brightness: Brightness


D65 = np.array(
    [
        [0.4124, 0.3576, 0.1805],
        [0.2126, 0.7152, 0.0722],
        [0.0193, 0.1192, 0.9505],
    ]
)

D65_INV = np.array(
    [
        [3.2406255, -1.5372080, -0.4986268],
        [-0.9689307, 1.8757561, 0.0415175],
        [0.0557101, -0.2040211, 1.0569959],
    ]
)


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
    def hex_to_rgb(hex_color: str):
        b = bytes.fromhex(hex_color)
        if len(b) != 3:
            raise ValueError("should be rgb hex code")
        return np.fromiter(b, np.uint8) / 255

    @classmethod
    def rgb_gamma_correction(cls, rgb: np.ndarray):
        rgb = rgb.clip(0, None)
        return np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, (rgb / 12.92))

    @classmethod
    def rgb_reverse_gamma_correction(cls, rgb):
        rgb = rgb.clip(0, None)
        return np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(rgb, (1.0 / 2.4)) - 0.055).clip(0, 1)

    @staticmethod
    def rgb_to_XYZ(rgb):
        return D65 @ rgb

    @staticmethod
    def _XYZ_to_xyY(xyz):
        """
        raw xy and brightness
        """
        return xyz[:2, ...] / xyz.sum(axis=0), xyz[1]

    def XYZ_to_xyY(self, xyz):
        """
        Corrected xy and brightness
        """
        xy, b = self._XYZ_to_xyY(xyz)
        if xy.ndim > 1:
            points = map(Point, xy.T)
        else:
            points = [Point(xy)]

        result = []

        for point in points:
            if point.is_empty:
                result.append((np.nan, np.nan))
                continue
            if self.gamut.contains(point):
                result += point.coords
                continue
            result += nearest_points(self.gamut, point)[0].coords

        return np.array(result).squeeze(), b

    def rgb_to_xyY(self, rgb):
        if not isinstance(rgb, np.ndarray):
            rgb = np.array(rgb)
        rgb = rgb.T

        return self.XYZ_to_xyY(self.rgb_to_XYZ(self.rgb_gamma_correction(rgb)))

    def hex_to_xyY(self, hex_color: str):
        return self.rgb_to_xyY(self.hex_to_rgb(hex_color))

    @staticmethod
    def xyY_to_XYZ(xy, b: np.ndarray):
        if (b > 1).any():
            b /= 100
        x, y = xy
        z = 1 - x - y

        return np.array((b / y * x, b, b / y * z)).reshape(3, -1)

    @staticmethod
    def XYZ_to_rgb(xyz):
        return D65_INV @ xyz

    @classmethod
    def xyY_to_rgb(cls, xy, Y: Optional[Union[float, Sequence[float]]] = None):
        if not isinstance(xy, np.ndarray):
            xy = np.array(xy).T

        if Y is None:
            Y = np.ones(xy.shape[1])
        elif isinstance(Y, float):
            Y = np.array([Y])
        elif not isinstance(Y, np.ndarray):
            Y = np.array(Y)

        return cls.rgb_reverse_gamma_correction(cls.XYZ_to_rgb(cls.xyY_to_XYZ(xy, Y)))

    @staticmethod
    def rgb_to_hex(rgb):
        return bytes(rgb).hex()

    @classmethod
    def xyY_to_hex(cls, xy, Y: Optional[Union[float, Sequence[float]]] = None) -> Union[str, Sequence[str]]:
        rgb = np.round(cls.xyY_to_rgb(xy, Y) * 255).clip(0, 255).astype(np.uint8).T.squeeze()

        if rgb.ndim > 1:
            return [cls.rgb_to_hex(c) for c in rgb]
        return cls.rgb_to_hex(rgb)
