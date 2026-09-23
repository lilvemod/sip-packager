""" 
Tool for extracting adjusted classification data from an Excel file and saving it as key-value pairs in a JSON-file that is then read by cits-erms.py to create the title element in the ERMS XML.
"""
import json
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
# Change filename if needed
FILE_TO_READ = "Verktyg1.xlsx"
KLASSA_SOURCE_PATH = BASE_DIR / "config" / FILE_TO_READ


def main():
    df = pd.read_excel(KLASSA_SOURCE_PATH, header=None)

    result = {}

    # Requires the input to be formatted as the examples found in config.
    # Takes the first three columns that together make up the classification as key, then takes the fifth row (E) with its process as corresponding value.
    for _, row in df.iterrows():
        a = row[0]
        b = row[1]
        c = row[2]
        process = row[4]

        # Skip rows where C is NaN
        if pd.isna(c):
            continue

        key = f"{int(a)}.{int(b)}.{int(c)}"

        if isinstance(process, str) and process.strip():
            result[key] = process.strip()


    OUTPUT_JSON_PATH = BASE_DIR / "config" / "klassa_processer.json"
    OLD_JSON_PATH = BASE_DIR / "config" / "klassa_processer_OLD"

    # Handle the output of a new json config file, and if an old one exists, rename it to klassa_processer_OLD.json
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


