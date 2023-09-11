import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.widgets import PolygonSelector

HELPER = """Enclose cells within a polygon. Helper:
    - Click on the plot to add a polygon vertex
    - Press the 'esc' key to start a new polygon
    - Try holding the 'ctrl' key to move a single vertex
    - Once the polygon is finished and overlaid in red, you can close the window
"""

VALID_N_CHANNELS = [1, 3]


class _Selector:
    def __init__(self, ax):
        self.poly = PolygonSelector(ax, self.onselect, draw_bounding_box=True)
        print(HELPER)
        plt.show()

    def onselect(self, vertices):
        self.vertices = vertices
        print(f"\nVertices: {self.vertices}")

    def disconnect(self):
        self.poly.disconnect_events()


def _save_polygon(path: str, selector: _Selector):
    with open(path, "w") as f:
        json.dump(selector.vertices, f, indent=4)


def xarr_selector(
    image_path: str,
    output_path: str,
    channels: list[str] | str | None,
    scale_factor: float = 10,
    margin_ratio: float = 0.2,
):
    import xarray as xr

    from .image import resize

    image = xr.open_zarr(image_path)["image"]

    if channels is not None:
        assert (
            isinstance(channels, str) or len(channels) in VALID_N_CHANNELS
        ), f"Number of channels provided must be in: {', '.join(VALID_N_CHANNELS)}"
        image = image.sel(c=channels).transpose("y", "x", "c")

    image = resize(image, scale_factor).compute()

    _, ax = plt.subplots()
    ax.imshow(image)

    dy, dx, *_ = image.shape
    plt.xlim(-margin_ratio * dx, dx + margin_ratio * dx)
    plt.ylim(dy + margin_ratio * dy, -margin_ratio * dy)

    selector = _Selector(ax)
    _save_polygon(output_path, selector)


def cells_selector(
    metadata_path: str, output_path: str, x: str = "center_x", y: str = "center_y"
):
    df = pd.read_csv(metadata_path)

    _, ax = plt.subplots()
    ax.scatter(
        df[x],
        df[y],
        marker=".",
        rasterized=True,
        s=0.05,
    )

    selector = _Selector(ax)

    _save_polygon(output_path, selector)


def main(args):
    VALID_SUFFIX = [".zarr", ".csv"]

    path = Path(args.input)

    assert (
        path.suffix in VALID_SUFFIX
    ), f"Valid input suffix are: {', '.join(VALID_SUFFIX)}"

    if path.suffix == ".zarr":
        xarr_selector(path, args.polygon, args.channels)
    if path.suffix == ".csv":
        cells_selector(path, args.polygon)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Path to input file, either a cell_metadata.csv file, or a xarray .zarr file",
    )
    parser.add_argument(
        "-p",
        "--polygon",
        type=str,
        required=True,
        help="Path where the polygon will be saved",
    )
    parser.add_argument(
        "-c",
        "--channels",
        type=str,
        nargs="+",
        default=None,
        help="List of channels name to be displayed",
    )

    main(parser.parse_args())
