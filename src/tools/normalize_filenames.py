"""
Normalize filenames to comply with FGS package standards.
"""

import os
import json
import sys
import logging
from pathlib import Path

# Allowed characters according to FGS
ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"

# Simply replaces common diacritic characters in the swedish language with its most basic counterpart
REPLACE_MAP = {
    "å": "a", "ä": "a", "ö": "o",
    "Å": "A", "Ä": "A", "Ö": "O"
}

def determine_project_root() -> Path:
    """
    Determine the project root by checking where the config folder exists.
    """
    root = Path(__file__).resolve().parents[2]
    if not (root / "config").exists():
        root = Path(__file__).resolve().parents[1]
    return root


def load_run_config(project_root: Path) -> dict:
    """
    Load run_config.json from the project config folder.
    """
    config_path = project_root / "config" / "run_config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"run_config.json is missing: {config_path}")

    try:
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        raise ValueError(f"Could not read run_config.json: {exc}")



def setup_logging(verbose: bool) -> None:
    """Configure logging output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )


def sanitize_filename(filename: str) -> str:
    """Return a sanitized filename as a string."""
    new_name = []
    for char in filename:
        if char in ALLOWED_CHARS:
            new_name.append(char)
        else:
            new_name.append(REPLACE_MAP.get(char, "_"))
    return "".join(new_name)


def ensure_unique_path(folder: Path, filename: str) -> str:
    """
    Ensure the filename is unique inside the folder.
    """
    base, ext = os.path.splitext(filename)
    counter = 1
    new_name = filename

    while (folder / new_name).exists():
        new_name = f"{base}_{counter}{ext}"
        counter += 1

    return new_name


def normalize_filenames(root_path: Path) -> int:
    """
    Normalize filenames under the given root path. Returns number of changed files.
    """
    if not root_path.exists():
        raise FileNotFoundError(f"Root path does not exist: {root_path}")

    if not root_path.is_dir():
        raise NotADirectoryError(f"Root path is not a directory: {root_path}")

    changed_files = 0

    for folder, subfolders, files in os.walk(root_path):
        folder_path = Path(folder)

        for file in files:
            sanitized = sanitize_filename(file)

            if sanitized != file:
                unique_name = ensure_unique_path(folder_path, sanitized)

                old_path = folder_path / file
                new_path = folder_path / unique_name

                try:
                    os.rename(old_path, new_path)
                    logging.info(f"Renamed: {file} → {unique_name}")
                    changed_files += 1

                except PermissionError:
                    logging.warning(
                        f"Could not rename '{file}' because it is open in another program."
                    )
                except OSError as exc:
                    logging.error(f"Failed to rename '{file}': {exc}")

    return changed_files


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Normalize filenames according to FGS allowed characters."
    )
    parser.add_argument(
        "--root",
        type=str,
        help="Root folder to run on. If no cli, the sip_root is determined by run_config.json."
        )
    
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose logging."
        )
    args = parser.parse_args(argv)

    setup_logging(args.verbose)

    try:
        project_root = determine_project_root()
        config = load_run_config(project_root)
    except Exception as exc:
        logging.error(f"Failed to load run_config.json: {exc}")
        return 1

    root_path = Path(args.root) if args.root else Path(config["sip_root"])

    try:
        changed = normalize_filenames(root_path)

        if changed == 0:
            logging.info("No files contained disallowed characters. Exiting.")
            return 0

        logging.info(f"Done. {changed} files were renamed in {root_path}.")
        return 0

    except Exception as exc:
        logging.error(f"Fatal error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
