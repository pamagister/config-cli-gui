class Color:
    """Simple color class for RGB values."""

    def __init__(self, r: int = 0, g: int = 0, b: int = 0):
        self.r = max(0, min(255, r))
        self.g = max(0, min(255, g))
        self.b = max(0, min(255, b))

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

    @classmethod
    def from_hex(cls, hex_color: str) -> "Color":
        hex_color = hex_color.lstrip("#")
        if len(hex_color) == 6:
            return cls(
                int(hex_color[0:2], 16),
                int(hex_color[2:4], 16),
                int(hex_color[4:6], 16),
            )
        return cls()

    def __str__(self):
        return self.to_hex()

    def __repr__(self):
        return f"Color({self.r}, {self.g}, {self.b})"
