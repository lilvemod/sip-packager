"""
Tool for extracting adjusted classification data from an Excel file and saving it
as key-value pairs in a JSON file that is then read by cits-erms.py.
"""

import datetime
import json
import logging
import sys
from pathlib import Path
import pandas as pd

from src.common.utils import (
    parse_args,
    setup_logging,
    determine_project_root,
)


DEFAULT_FILE_TO_READ = "Klassa_2_1.xlsx"
DEFAULT_CANDIDATE_FILENAME = "klassa_processer_OLD"


def validate_excel_file(path: Path) -> pd.DataFrame:
    """
    Validate that the file exists, is an Excel file, can be read, and has enough columns.
    The input must follow the structure and data types of the example XSLSX file found under config/
    """

    if not path.exists():
        logging.error("File %s was not found in config/.", path.name)
        raise FileNotFoundError(path)

    if path.suffix.lower() not in [".xlsx", ".xls"]:
        logging.error("File %s is not an Excel file (.xlsx or .xls).", path.name)
        raise ValueError("Invalid extension")

    try:
        df = pd.read_excel(path, header=None)
    except Exception as e:
        logging.error("File %s could not be read as an Excel file.", path.name)
        logging.error("Details: %s", e)
        raise

    if df.shape[1] < 4:
        raise ValueError(
            f"Excel file must have at least 4 columns, but it has {df.shape[1]}."
        )

    logging.info("Excel file %s validated successfully.", path.name)
    return df


def transform_df_to_mapping(rows) -> dict:
    """
    Transform the data frame into key-value pairs.
    The data is structured into four columns in the xlsx file. The first three are single digits that together identify a unique designation
    within the classification structure, the fourth is a textual description of what the designation points to.
    """
    result = {}

    # vt is short for verksamhetstyp, vo for verksamhetsområde and pg for processgrupp
    for _, row in rows:
        vt, vo, pg, process = row[0], row[1], row[2], row[3]

        if not isinstance(process, str) or not process.strip():
            continue

        # If the value of the third row is NaN, then only count the first two. This is true everytime a verksamhetsområde is found in the data.
        # The logic can be extended if the data has to support a structure down to the fourth level (processes).
        if pd.isna(pg):
            key = f"{int(vt)}.{int(vo)}"
        else:
            key = f"{int(vt)}.{int(vo)}.{int(pg)}"

        result[key] = process.strip()

    return result


def backup_old_json(output_path: Path):
    """
    Prevent file collision if there already is a klassa_processer.json file in the config folder.
    """
    if output_path.exists():
        base = output_path.parent / DEFAULT_CANDIDATE_FILENAME
        candidate = base.with_suffix(".json")
        counter = 0

        while candidate.exists():
            counter += 1
            candidate = output_path.parent / f"{DEFAULT_CANDIDATE_FILENAME}_{counter}.json"

        output_path.rename(candidate)
        logging.info("Existing JSON backed up as: %s", candidate)


def write_output_json(mapping: dict, output_path: Path):
    """
    Write the mapped data to key-value pairs in a json-file.
    """
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=4)

    logging.info("JSON-file created: %s", output_path)


def main(argv=None):
    args = parse_args(argv)
    setup_logging(args.verbose)

    start_time = datetime.datetime.now()

    try:
        project_root = determine_project_root()
        config_dir = project_root / "config"

        # Determine input file
        file_to_read = args.root if args.root else DEFAULT_FILE_TO_READ
        excel_path = config_dir / file_to_read

        # Read the data from the excel file
        df = validate_excel_file(excel_path)

        # Transform to a mapping
        mapping = transform_df_to_mapping(df.iterrows())

        # Set where the output should be saved and handle possible file collisions when the file is saved
        output_path = config_dir / "klassa_processer.json"
        backup_old_json(output_path)

        # Takes the transformed mapping, converts it into key-value pairs that are saved in a JSON file at the appointed path
        write_output_json(mapping, output_path)

        # Stops the clock for runtime
        elapsed = datetime.datetime.now() - start_time

        logging.info(
            f"Done. The program {Path(__file__).name} took {elapsed.total_seconds():.2f} seconds to run"
        )
        return 0

    except Exception as exc:
        logging.error("Failed to generate JSON: %s", exc, exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
