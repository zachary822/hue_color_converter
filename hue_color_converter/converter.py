from collections.abc import Sequence
from typing import Optional, Union

import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points

from hue_color_converter.gamuts import DEFAULT_GAMUT, get_gamut

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


class BaseConverter:
    def __init__(self, gamut: Union[list[tuple[float, float]], Polygon, None] = None):
        if gamut is None:
            self.gamut = DEFAULT_GAMUT
        elif isinstance(gamut, list):
            self.gamut = Polygon(gamut)
        elif isinstance(gamut, Polygon):
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
        return np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(rgb, (1.0 / 2.4)) - 0.055)

    @staticmethod
    def rgb_to_xyz(rgb):
        return D65 @ rgb

    @staticmethod
    def _xyz_to_xyy(xyz):
        """
        raw xy and brightness
        """
        return xyz[:2, ...] / xyz.sum(axis=0), xyz[1]

    def xyz_to_xyy(self, xyz):
        """
        Corrected xy and brightness
        """
        xy, Y = self._xyz_to_xyy(xyz)
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

        return np.array(result).squeeze(), Y

    def rgb_to_xyy(self, rgb):
        if not isinstance(rgb, np.ndarray):
            rgb = np.array(rgb)
        rgb = rgb.T

        if rgb.shape[0] != 3:
            raise ValueError("rgb should be arranged column wise")
        return self.xyz_to_xyy(self.rgb_to_xyz(self.rgb_gamma_correction(rgb)))

    def hex_to_xyy(self, hex_color: str):
        return self.rgb_to_xyy(self.hex_to_rgb(hex_color))

    @staticmethod
    def xyy_to_xyz(xy, b: np.ndarray):
        if (b > 1).any():
            b /= 100
        x, y = xy
        z = 1 - x - y

        return np.array((b / y * x, b, b / y * z)).reshape(3, -1)

    @staticmethod
    def xyz_to_rgb(xyz, scale: bool = False):
        rgb = D65_INV @ xyz

        if scale:
            col_max = rgb.max(axis=0)
            rgb /= np.where(col_max > 1, col_max, 1)  # scale if rgb values > 1
            return rgb

        return rgb.clip(0, 1)

    @classmethod
    def xyy_to_rgb(cls, xy, Y: Optional[Union[float, Sequence[float]]] = None, scale: bool = False):
        if not isinstance(xy, np.ndarray):
            xy = np.array(xy)
        xy = xy.T

        if Y is None:
            Y = np.ones(xy.shape[1])
        elif isinstance(Y, float):
            Y = np.array([Y])
        elif not isinstance(Y, np.ndarray):
            Y = np.array(Y)

        return cls.rgb_reverse_gamma_correction(cls.xyz_to_rgb(cls.xyy_to_xyz(xy, Y), scale=scale))

    @staticmethod
    def rgb_to_hex(rgb):
        return bytes(rgb).hex()

    @classmethod
    def xyy_to_hex(
        cls, xy, Y: Optional[Union[float, Sequence[float]]] = None, scale: bool = False
    ) -> Union[str, Sequence[str]]:
        rgb = np.round(cls.xyy_to_rgb(xy, Y, scale=scale) * 255).clip(0, 255).astype(np.uint8).T.squeeze()

        if rgb.ndim > 1:
            return [cls.rgb_to_hex(c) for c in rgb]
        return cls.rgb_to_hex(rgb)


class Converter(BaseConverter):
    def __init__(self, gamut: Union[str, list[tuple[float, float]], Polygon, None] = None):
        if isinstance(gamut, str):
            gamut = get_gamut(gamut)
        super().__init__(gamut=gamut)
