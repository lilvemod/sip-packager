"""
Common methods used by several programs in the project.
"""

import argparse
import json
import logging
from lxml import etree
from pathlib import Path

# ----------------------------------------
# Function to allow for command-line arguments that override the default paths from run_config and the logging level to debugger
# ----------------------------------------


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Handles up to three command-line arguments, with some variations between uses"
    )

    parser.add_argument(
        "--root",
        type=str,
        help="See the use of the function in the program that makes use of it."
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        help="See the use of the function in the program that makes use of it."
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Sets logging to debug-mode."
    )

    return parser.parse_args(argv)


# ----------------------------------------
# Logging
# ----------------------------------------
def setup_logging(verbose: bool):
    # Logging is set to print down to INFO as default, DEBUG if -v or --verbose is ran as an additional argument at runtime
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )


# ----------------------------------------
# Project root detection
# ----------------------------------------
def determine_project_root() -> Path:
    root = Path(__file__).resolve().parents[2]
    if not (root / "config").exists():
        root = Path(__file__).resolve().parents[1]
    return root


# ----------------------------------------
# Root path validation
# ----------------------------------------
def validate_root_path(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Root path does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"Root path is not a directory: {path}")

# ----------------------------------------
# Load the run_config.json file
# ----------------------------------------


def load_run_config(project_root: Path) -> dict:
    path = project_root / "config" / "run_config.json"
    logging.debug("Loading run_config from: %s", path)

    if not path.exists():
        raise FileNotFoundError("run_config.json is missing: %s", path)

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

# ----------------------------------------
# Load the submission_agreement.json file
# ----------------------------------------


def load_submission_agreement(project_root: Path) -> dict:
    path = project_root / "config" / "profiles" / "submission_agreement.json"
    logging.debug("Loading submission_agreement from: %s", path)

    if not path.exists():
        raise FileNotFoundError("submission_agreement.json is missing: %s", path)

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

# ----------------------------------------
# Load the klassa_processer.json file
# ----------------------------------------


def load_klassa_processer(project_root: Path) -> dict:
    path = project_root / "config" / "klassa_processer.json"
    logging.debug("Loading klassa_processer from: %s", path)

    if not path.exists():
        raise FileNotFoundError("klassa_processer.json is missing: %s", path)

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

# ----------------------------------------
# Write XML as output (with pretty print)
# ----------------------------------------


def write_xml(tree: etree.ElementTree, output_path: Path) -> None:
    if output_path.exists() and output_path.is_dir():
        raise IsADirectoryError("Output path is a directory: %s", output_path)

    if output_path.parent and not output_path.parent.exists():
        raise FileNotFoundError("Output directory does not exist: %s", output_path.parent)

    logging.debug("Writing XML to: %s", output_path)

    pretty_xml = etree.tostring(
        tree,
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8"
    )

    with output_path.open("wb") as f:
        f.write(pretty_xml)