import os
from pathlib import Path
from typing import Any

from PIL import ImageFont

from config_cli_gui.configtypes.color import Color


def list_system_fonts() -> list[str]:
    font_dirs = [
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        str(Path.home() / ".fonts"),
        "/Library/Fonts",
        "/System/Library/Fonts",
        "C:/Windows/Fonts",
    ]

    fonts: list[str] = []
    for d in font_dirs:
        if os.path.isdir(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith((".ttf", ".otf")):
                        fonts.append(os.path.join(root, f))
    return fonts


class Font:
    """Represents a font with type, size and color."""

    # Klassenattribute nach Klassendefinition setzen
    font_files = list_system_fonts()
    font_names = sorted([os.path.basename(f) for f in font_files])
    font_files_sorted = sorted(font_files, key=os.path.basename)

    def __init__(self, font_type: str, size: float, color: "Color"):
        self.name = font_type
        self.size = size
        self.color = color

    def to_list(self) -> list[Any]:
        return [self.name, self.size, self.color.to_hex()]

    @classmethod
    def from_list(cls, font_data: list[Any]) -> "Font":
        if len(font_data) < 3:
            return cls("Arial", 12, Color(0, 0, 0))

        font_type, size, color_val = font_data
        color = (
            Color.from_hex(color_val) if isinstance(color_val, str) else Color.from_list(color_val)
        )
        return cls(str(font_type), float(size), color)

    def get_image_font(self, dpi=25.4) -> ImageFont.FreeTypeFont:
        """
        Return a PIL FreeTypeFont, with fallback to default.

        :param dpi: if dpi is provided, the font size is re-calculated on base of the dpi
        :return:
        """
        try:
            if self.name in self.font_names:
                idx = self.font_names.index(self.name)
                path = self.font_files_sorted[idx]
                size = self.size * dpi / 25.4
                return ImageFont.truetype(path, size)
        except Exception as e:
            print(f"Fehler beim Laden der Schrift '{self.name}': {e}")

        print("Fallback: Nutze Default-Font.")
        return ImageFont.load_default()

    def __repr__(self) -> str:
        return f"Font(type='{self.name}', size={self.size}, color={self.color!r})"

    def __str__(self) -> str:
        return f"{self.name}, {self.size}pt, {self.color}"
