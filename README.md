# Philips Hue Color Converter  (CIE xy)

```python
from hue_color_converter import Converter

converter = Converter()  # optionally provide device id or "A", "B", "C" color gamut for more accurate colors

(x, y), brightness = converter.hex_to_xyb("ff00ff")
# calculated brightness is on the scale of 0-1

converter.xyb_to_hex(x=0.3209, y=0.1541, brightness=1)
```

Click [here](https://developers.meethue.com/develop/hue-api/supported-devices/) to see which color gamuts are supported for your device.
