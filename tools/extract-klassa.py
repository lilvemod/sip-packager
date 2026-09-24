""" 
Tool for extracting adjusted classification data from an Excel file and saving it as key-value pairs in a JSON-file that is then read by cits-erms.py to create the title element in the ERMS XML.
"""
import json
import logging
from pathlib import Path
import pandas as pd
import sys


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_FILE_TO_READ = "Verktyg1.xlsx"

# The file to read can be specified as a command line argument, otherwise the default file will be used.
FILE_TO_READ = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_FILE_TO_READ
KLASSA_SOURCE_PATH = BASE_DIR / "config" / FILE_TO_READ

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)

def validate_excel_file(path: Path) -> pd.DataFrame:
    """Validate that the file exists, is an Excel file, can be read, and has enough columns."""

    # 1. File exists
    if not path.exists():
        logger.error(f"File '{path.name}' was not found in config/.")
        sys.exit(1)

    # 2. Check if file has the correct extension
    if path.suffix.lower() not in [".xlsx", ".xls"]:
        logger.error(f"File '{path.name}' is not an Excel file (.xlsx or .xls).")
        sys.exit(1)

    # 3. Try reading the file
    try:
        klassa_input = pd.read_excel(path, header=None)
    except Exception as e:
        logger.error(f"File '{path.name}' could not be read as an Excel file.")
        logger.error(f"Details: {e}")
        sys.exit(1)

    # 4. Check minimum number of columns
    if klassa_input.shape[1] < 4:
        logger.error(
            f"Excel file must have at least 4 columns, but it has {klassa_input.shape[1]}."
        )
        sys.exit(1)

    logger.info(f"Excel file '{path.name}' validated successfully.")
    return klassa_input

def main():
    klassa_input = validate_excel_file(KLASSA_SOURCE_PATH)

    result = {}

    # Requires the input to be formatted as the examples found in config.
    # Takes the first three columns that together make up the classification as key, then takes the fourth row (D) with its process as corresponding value.
    for _, row in klassa_input.iterrows():
        a = row[0]
        b = row[1]
        c = row[2]
        process = row[3]

        if not isinstance(process, str) or not process.strip():
            continue

        # Handler for cases where the third column is empty
        if pd.isna(c):
            key= f"{int(a)}.{int(b)}"
        else:
            key = f"{int(a)}.{int(b)}.{int(c)}"
        
        result[key] = process.strip()


    OUTPUT_JSON_PATH = BASE_DIR / "config" / "klassa_processer.json"
    OLD_JSON_PATH = BASE_DIR / "config" / "klassa_processer_OLD"

    # Handles the output of a new json config file, and if an old one exists, rename it to klassa_processer_OLD.json
    if OUTPUT_JSON_PATH.exists():
        counter = 0
        candidate = OLD_JSON_PATH.with_suffix(".json")

        while candidate.exists():
            counter += 1
            candidate = BASE_DIR / "config" / f"klassa_processer_OLD_{counter}.json"

        OUTPUT_JSON_PATH.rename(candidate)

    with OUTPUT_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print(f"JSON-file created: {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    main()


