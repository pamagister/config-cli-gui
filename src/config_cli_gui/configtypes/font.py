import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from PIL import ImageFont

from config_cli_gui.configtypes.color import Color

logger = logging.getLogger("config_cli_gui")

FONT_EXTENSIONS = (".ttf", ".otf", ".ttc", ".woff", ".woff2")


def list_system_fonts() -> list[str]:
    # Common font directories on Linux, macOS, Windows
    font_dirs = [
        # Linux
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        str(Path.home() / ".fonts"),
        str(Path.home() / ".local/share/fonts"),
        # macOS system + user
        "/Library/Fonts",
        "/System/Library/Fonts",
        str(Path.home() / "Library/Fonts"),
        "/Network/Library/Fonts",
        # Windows system + user-scoped installed fonts
        "C:/Windows/Fonts",
        str(Path(os.environ.get("LOCALAPPDATA", "") + "/Microsoft/Windows/Fonts")),
    ]

    fonts: list[str] = []
    seen = set()  # Prevent duplicates

    for d in font_dirs:
        if d and os.path.isdir(d):
            for root, _, files in os.walk(d):
                for f in files:
                    if f.lower().endswith(FONT_EXTENSIONS):
                        full = os.path.join(root, f)
                        if full not in seen:
                            seen.add(full)
                            fonts.append(full)

    return fonts


@lru_cache(maxsize=1)
def _font_index() -> tuple[list[str], list[str], list[str]]:
    """Scan the system fonts once, on first access."""
    font_files = list_system_fonts()
    font_names = sorted(os.path.basename(f) for f in font_files)
    font_files_sorted = sorted(font_files, key=os.path.basename)
    return font_files, font_names, font_files_sorted


class _LazyFontList:
    """Class attribute that triggers the font scan only when it is read."""

    def __init__(self, index: int):
        self.index = index

    def __get__(self, obj: Any, owner: Any = None) -> list[str]:
        return _font_index()[self.index]


class Font:
    """Represents a font with type, size and color."""

    # Scanned lazily: importing this module must not walk the file system.
    font_files = _LazyFontList(0)
    font_names = _LazyFontList(1)
    font_files_sorted = _LazyFontList(2)

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

        font_type, size, color_val = font_data[:3]
        color = (
            Color.from_hex(color_val) if isinstance(color_val, str) else Color.from_list(color_val)
        )
        return cls(str(font_type), float(size), color)

    def to_str(self) -> str:
        return f"{self.name}, {self.size}, {self.color.to_hex()}"

    @classmethod
    def from_str(cls, font_init_str: str) -> "Font":
        """
        Parses a string of the form:
            "FontName, size, #rrggbb"
        or alternative color formats.
        """
        if not isinstance(font_init_str, str):
            return cls("Arial", 12, Color(0, 0, 0))

        parts = [p.strip() for p in font_init_str.split(",")]

        # at least name, size, color
        if len(parts) < 3:
            return cls("Arial", 12, Color(0, 0, 0))

        # parse font name
        font_name = parts[0]

        # parse size
        try:
            size = float(parts[1])
        except ValueError:
            size = 12.0

        # parse color
        color_raw = ",".join(parts[2:]).strip()
        color = Color.from_hex(color_raw)

        return cls(font_name, size, color)

    def get_font_path(self) -> str | None:
        """Return the file path of this font if it is installed, else None."""
        if os.path.isfile(self.name):
            return self.name
        names = self.font_names
        if self.name in names:
            return self.font_files_sorted[names.index(self.name)]
        return None

    def get_image_font(self, dpi=25.4) -> ImageFont.FreeTypeFont:
        """
        Return a PIL FreeTypeFont, with fallback to default.

        :param dpi: if dpi is provided, the font size is re-calculated on base of the dpi
        :return:
        """
        size = self.size * dpi / 25.4
        # Unknown names are still passed to Pillow, which searches the system font dirs itself.
        for candidate in (self.get_font_path() or self.name, "Arial.ttf", "DejaVuSans.ttf"):
            try:
                return ImageFont.truetype(font=candidate, size=size)
            except OSError as e:
                logger.debug(f"Could not load font '{candidate}': {e}")

        logger.warning(f"Font '{self.name}' not found, using Pillow default font.")
        return ImageFont.load_default(size=size)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Font):
            return NotImplemented
        return (self.name, float(self.size), self.color) == (
            other.name,
            float(other.size),
            other.color,
        )

    def __hash__(self) -> int:
        return hash((self.name, float(self.size), self.color))

    def __repr__(self) -> str:
        return f"Font(type='{self.name}', size={self.size}, color={self.color!r})"

    def __str__(self) -> str:
        return f"{self.to_str()}"
