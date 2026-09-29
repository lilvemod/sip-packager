"""
The program creates a CSIP file structure and copies the folders and underlying files from the input path there.
"""

import logging
import shutil
from pathlib import Path
from src.common.utils import (
    parse_args,
    setup_logging,
    determine_project_root,
    validate_root_path,
    load_run_config
)


def validate_erms_file_count(erms_input: Path, max_files: int) -> None:
    """
    Count all files under erms_input. If the number exceeds max_files,
    raise an exception to stop execution.
    """
    validate_root_path(erms_input)

    file_count = sum(1 for p in erms_input.rglob("*") if p.is_file())

    logging.info("Number of files in input: %d", file_count)

    if file_count > max_files:
        raise ValueError(
            "The folder contains %d files which exceeds the limit: %d. "
            "Aborts the program to avoid future complications.", file_count, max_files
        )


def rename_existing_sip_folder(sip_root: Path) -> None:
    """
    If the SIP folder already exists rename it to avoid file collisions
    """
    if not sip_root.exists():
        return

    # Since none of the programs ever remove any files or directories, the SIP root folder still exists after run_sip_packager has been run.
    # In case the user forgets to clear out the SIP folder before running the program again, the previous SIP root folder gets renamed so that the two don't get their contents mixed up.

    base = sip_root.parent
    old_name = "SIP_OLD"
    candidate = base / old_name
    counter = 1

    # Find next available name
    while candidate.exists():
        counter += 1
        candidate = base / f"{old_name}_{counter}"

    logging.warning("SIP-folder already exists. Renames to: %s", candidate)
    sip_root.rename(candidate)


def create_csip_structure(sip_root: Path) -> None:
    """
    Create the CSIP folder structure.
    """
    logging.debug("Creating CSIP structure at: %s", sip_root)

    # These are the baseline subfolders in CSIP. If there is a need to expand, do so here.
    (sip_root / "metadata").mkdir(parents=True, exist_ok=True)
    (sip_root / "documentation").mkdir(parents=True, exist_ok=True)
    (sip_root / "schemas").mkdir(parents=True, exist_ok=True)
    (sip_root / "representations" / "rep_001").mkdir(parents=True, exist_ok=True)


def copy_schemas(project_root: Path, sip_root: Path) -> None:
    """
    Copy all schemas from src/schemas to SIP/schemas.
    """

    # All schemas exist within the project to make sure that the correct versions are being used when running the program.
    # Note that METS 1.12 makes use of an older version of XLINK that is not always the first one found when searching for the schema.
    source = project_root / "src" / "schemas"
    target = sip_root / "schemas"

    validate_root_path(source)

    logging.debug("Copies schemas %s to %s", source, target)

    for schema in source.glob("*"):
        if schema.is_file():
            shutil.copy(schema, target)


def copy_erms_input(erms_input: Path, sip_root: Path) -> None:
    """
    Copy ERMS input folders (e.g. 1.1.1, 2.3.4) into SIP/representations/rep_001.
    """
    validate_root_path(erms_input)

    # Note that this implementation only ever makes use of one representation, but that this rep in turn can contain subfolders.

    target = sip_root / "representations" / "rep_001"

    logging.info("Copies folders from %s to %s", erms_input, target)

    for folder in erms_input.iterdir():
        if folder.is_dir():
            shutil.copytree(folder, target / folder.name, dirs_exist_ok=True)


def main(argv=None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)

    try:
        project_root = determine_project_root()
        config = load_run_config(project_root)
    except Exception as exc:
        logging.error("Could not load run_config.json: %s", exc)
        return 1

    # Path to where the CSIP structure should be created
    sip_root = Path(args.root) if args.root else Path(config["sip_root"])

    # Path to the folder containing subfolders to be copied over.
    erms_input = Path(args.output) if args.output else Path(config["erms_input"])

    # No fallback is set since the the program throws an exception if it can't read from config
    max_files = config.get("maximum_files")

    logging.info("SIP-root: %s", sip_root)
    logging.info("ERMS-input: %s", erms_input)

    try:
        validate_erms_file_count(erms_input, max_files)
        rename_existing_sip_folder(sip_root)
        create_csip_structure(sip_root)
        copy_schemas(project_root, sip_root)
        copy_erms_input(erms_input, sip_root)

        logging.info("CSIP structure has been successfully created.")
        return 0

    except Exception as exc:
        logging.error("Failed in creating CSIP structure: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
