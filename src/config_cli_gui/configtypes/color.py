class Color:
    """Simple color class for RGB values."""

    def __init__(self, r: int = 0, g: int = 0, b: int = 0):
        self.r = max(0, min(255, int(r)))
        self.g = max(0, min(255, int(g)))
        self.b = max(0, min(255, int(b)))

    def to_list(self) -> list[int]:
        return [self.r, self.g, self.b]

    def to_rgb(self) -> tuple[float, float, float]:
        return self.r / 255, self.g / 255, self.b / 255

    def to_pil(self) -> tuple[int, ...]:
        """Convert Color object to Pillow-compatible RGB tuple."""
        return tuple(int(c) for c in self.to_list())

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    @classmethod
    def from_list(cls, rgb_list: list[int | str]) -> "Color":
        if len(rgb_list) >= 3:
            return cls(int(rgb_list[0]), int(rgb_list[1]), int(rgb_list[2]))
        return cls()

    @staticmethod
    def is_valid_hex(hex_color: str) -> bool:
        """Return True if ``hex_color`` is a ``#rrggbb`` or ``#rgb`` string."""
        if not isinstance(hex_color, str):
            return False
        digits = hex_color.strip().lstrip("#")
        if len(digits) not in (3, 6):
            return False
        try:
            int(digits, 16)
        except ValueError:
            return False
        return True

    @classmethod
    def from_hex(cls, hex_color: str) -> "Color":
        """Parse ``#rrggbb`` or ``#rgb``; invalid input yields black."""
        if not cls.is_valid_hex(hex_color):
            return cls()
        digits = hex_color.strip().lstrip("#")
        if len(digits) == 3:
            digits = "".join(c * 2 for c in digits)
        return cls(int(digits[0:2], 16), int(digits[2:4], 16), int(digits[4:6], 16))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color):
            return NotImplemented
        return self.to_list() == other.to_list()

    def __hash__(self) -> int:
        return hash((self.r, self.g, self.b))

    def __str__(self):
        return self.to_hex()

    def __repr__(self):
        return f"Color({self.r}, {self.g}, {self.b})"
