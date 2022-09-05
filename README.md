# Philips Hue Color Converter  (CIE xyY)

Converts RGB to CIE xyY for Philips Hue

```python
from hue_color_converter import Converter

converter = Converter()  # optionally provide device id or "A", "B", "C" color gamut for more accurate colors

(x, y), Y = converter.hex_to_xyY("ff00ff")
# calculated brightness is on the scale of 0-1

converter.xyY_to_hex((0.3209, 0.1541), Y=0.2848)
```

Click [here](https://developers.meethue.com/develop/hue-api/supported-devices/) to see which color gamuts are supported for your device.

## Installing hue-color-converter

```shell
pip install hue-color-converter
```

## License

[MIT](./LICENSE.txt)
