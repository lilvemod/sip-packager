"""
Creates a ZIP file of the SIP folder. The ZIP filename is taken from the
OBJID attribute in mets.xml located directly under the SIP root.
Note that the program does not remove the folder SIP.
"""

import logging
from pathlib import Path
import xml.etree.ElementTree as ET
import sys
import zipfile
from src.common.utils import (
    parse_args,
    setup_logging,
    determine_project_root,
    validate_root_path,
    load_run_config
)


def extract_objid_from_mets(mets_path: Path) -> str:
    """
    Reads mets.xml and extracts the OBJID attribute.
    """
    if not mets_path.exists():
        raise FileNotFoundError(f"mets.xml not found at: {mets_path}")

    try:
        tree = ET.parse(mets_path)
        root = tree.getroot()
        objid = root.attrib.get("OBJID")

        if not objid:
            raise ValueError("OBJID attribute is missing in mets.xml")

        logging.info("OBJID extracted: %s", objid)
        return objid

    except Exception as exc:
        raise ValueError(f"Could not parse mets.xml: {exc}")


def zip_sip_folder(sip_root: Path, zip_path: Path) -> None:
    """
    Creates a ZIP file containing everything under sip_root.
    """
    logging.info("Creating ZIP: %s", zip_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in sip_root.rglob("*"):
            zipf.write(file_path, file_path.relative_to(sip_root))

    logging.info("ZIP file created successfully.")


def main(argv=None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)

    try:
        project_root = determine_project_root()
        config = load_run_config(project_root)
    except Exception as exc:
        logging.error("Could not load run_config.json: %s", exc)
        return 1

    sip_root = Path(args.root) if args.root else Path(config["sip_root"])
    validate_root_path(sip_root)

    mets_path = sip_root / "mets.xml"

    try:
        objid = extract_objid_from_mets(mets_path)
    except Exception as exc:
        logging.error("Failed to extract OBJID: %s", exc)
        return 1

    zip_filename = f"{objid}.zip"
    zip_path = sip_root.parent / zip_filename

    try:
        zip_sip_folder(sip_root, zip_path)
        logging.info("SIP zipped successfully: %s", zip_path)
        return 0

    except Exception as exc:
        logging.error("Failed to create ZIP: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
