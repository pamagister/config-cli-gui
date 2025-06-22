from pathlib import Path

NAME = "config_cli_gui"


class BaseGPXProcessor:
    def __init__(
        self,
        input_: str | Path | list[str],
        output=None,
        min_dist=10,
        date_format="%Y-%m-%d",
        elevation=True,
        logger=None,
    ):
        # ensure that input is converted into a list[Path]
        if isinstance(input_, str):
            self.input = [Path(input_)]
        elif isinstance(input_, Path):
            self.input = [input_]
        elif isinstance(input_, list):
            self.input = [Path(p) for p in input_ if isinstance(p, str | Path)]
        else:
            raise ValueError("Input must be a string, Path, or list of strings/Paths.")

        self.output = output
        self.min_dist = min_dist
        self.date_format = date_format
        self.include_elevation = elevation
        self.logger = logger

        # Initialize SRTM elevation data only if elevation is requested and SRTM is available
        self.elevation_data = None
        self.srtm_available = False

        self.logger.info(f"example module successfully initialized with input: {self.input}")

    def compress_files(self) -> list[Path]:
        """Shrink the size of all given gpx/kml files in se
        lf.input."""
        self.logger.info("successfully triggered function")
        return self.input

    def merge_files(self) -> list[Path]:
        """Merge all files of self.input into one gpx file with reduced resolution."""
        self.logger.info("successfully triggered function")
        return self.input

    def extract_pois(self) -> list[Path]:
        """Merge every starting point of each track in all files
        into one gpx file with many pois."""
        self.logger.info("successfully triggered function")
        return self.input
