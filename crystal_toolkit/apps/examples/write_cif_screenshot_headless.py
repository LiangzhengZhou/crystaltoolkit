from __future__ import annotations

import argparse
import time
import urllib
from multiprocessing import Process
from pathlib import Path

import dash
from dash import html
from dash.dependencies import Input, Output, State
from playwright.sync_api import sync_playwright
from pymatgen.core import Structure

import crystal_toolkit.components as ctc
from crystal_toolkit.settings import SETTINGS


def build_app(cif_path: Path, output_path: Path) -> dash.Dash:
    app = dash.Dash(assets_folder=SETTINGS.ASSETS_PATH)

    structure = Structure.from_file(cif_path)
    structure_component = ctc.StructureMoleculeComponent(
        structure,
        id="cif-structure",
        show_compass=False,
        bonded_sites_outside_unit_cell=True,
        scene_settings={"zoomToFit2D": True},
    )

    layout = html.Div([structure_component.layout(), html.Div(id="dummy-output")])

    @app.callback(
        Output(structure_component.id("scene"), "imageRequest"),
        Input(structure_component.id("graph"), "data"),
    )
    def trigger_image_request(data):  # noqa: ARG001
        return {"filetype": "png"}

    @app.callback(
        Output("dummy-output", "children"),
        Input(structure_component.id("scene"), "imageDataTimestamp"),
        State(structure_component.id("scene"), "imageData"),
    )
    def save_image(image_data_timestamp, image_data):  # noqa: ARG001
        if image_data:
            response = urllib.request.urlopen(image_data)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as file:
                file.write(response.file.read())

    ctc.register_crystal_toolkit(app=app, layout=layout)
    return app


def run_server(cif_path: Path, output_path: Path, host: str, port: int) -> None:
    app = build_app(cif_path, output_path)
    app.run_server(debug=False, host=host, port=port, use_reloader=False)


def capture_screenshot(
    url: str,
    output_path: Path,
    timeout_s: float,
    browser_path: str | None,
    headless: bool,
) -> None:
    output_path.unlink(missing_ok=True)
    with sync_playwright() as playwright:
        launch_kwargs = {"headless": headless}
        if browser_path:
            launch_kwargs["executable_path"] = browser_path
        browser = playwright.chromium.launch(**launch_kwargs)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        deadline = time.time() + timeout_s
        while time.time() < deadline and not output_path.exists():
            time.sleep(0.25)
        browser.close()

    if not output_path.exists():
        raise RuntimeError(f"Screenshot not created within {timeout_s} seconds.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render a CIF file to a PNG using Dash + Playwright (headless).",
    )
    parser.add_argument("cif_path", type=Path, help="Path to the CIF file.")
    parser.add_argument(
        "output_path",
        type=Path,
        nargs="?",
        default=Path("structure_dash.png"),
        help="Where to save the PNG screenshot.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for the Dash server.")
    parser.add_argument("--port", type=int, default=8050, help="Port for the Dash server.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Seconds to wait for the PNG to be written.",
    )
    parser.add_argument(
        "--browser-path",
        default=None,
        help="Optional path to a system Chromium/Chrome executable.",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run the browser in headed mode (not headless).",
    )
    args = parser.parse_args()

    server = Process(
        target=run_server,
        args=(args.cif_path, args.output_path, args.host, args.port),
    )
    server.start()

    try:
        url = f"http://{args.host}:{args.port}"
        capture_screenshot(
            url=url,
            output_path=args.output_path,
            timeout_s=args.timeout,
            browser_path=args.browser_path,
            headless=not args.headed,
        )
    finally:
        server.terminate()
        server.join()

    print(f"Saved screenshot to {args.output_path.resolve()}")


if __name__ == "__main__":
    main()
