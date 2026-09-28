"""
Normalize filenames to comply with FGS package standards.
"""

import sys
import logging
from pathlib import Path
from src.common.utils import (
    parse_args,
    setup_logging,
    determine_project_root,
    load_run_config,
)

# Allowed characters according to FGS
ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"

# Simply replaces common diacritic characters in the swedish language with its most basic counterpart
REPLACE_MAP = {
    "å": "a", "ä": "a", "ö": "o",
    "Å": "A", "Ä": "A", "Ö": "O"
}


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
    # The split is done so that counter can be added in between the stem and the extension
    p = Path(filename)
    base = p.stem
    ext = p.suffix

    counter = 1
    new_name = filename

    # Handles file name collisions. For example a file ää.txt and åå.txt would after normalization be aa.txt.
    # This adds a _x suffix each time. So instead of one aa.txt file, the program produces aa.txt and aa_1.txt based on the previous example.
    while (folder / new_name).exists():
        new_name = f"{base}_{counter}{ext}"
        counter += 1

    return new_name


def normalize_filenames(root_path: Path) -> int:
    """
    Normalize filenames under the given root path. Returns number of changed files.
    """

    # Counts how many files have been affected and produces the total count as terminal output when the program is done.
    changed_files = 0

    for folder_path in root_path.rglob("*"):
        if folder_path.is_file():
            file = folder_path.name
            sanitized = sanitize_filename(file)

            if sanitized != file:
                unique_name = ensure_unique_path(folder_path.parent, sanitized)

                old_path = folder_path
                new_path = folder_path.parent / unique_name

                try:
                    old_path.rename(new_path)
                    logging.debug(f"Renamed: {file} → {unique_name}")
                    changed_files += 1

                except PermissionError:
                    logging.warning(
                        f"Could not rename '{file}' because it is open in another program."
                    )
                except OSError as exc:
                    logging.error(f"Failed to rename '{file}': {exc}")

    return changed_files


def main(argv=None) -> int:
    args = parse_args(argv)
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
