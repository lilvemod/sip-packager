"""
Generate a CITS-ERMS 2.1.0 XML-file from a KLASSA 2.1-based folder structure.
"""

import argparse
import datetime
import logging
import json
import sys
from pathlib import Path
from lxml import etree
import uuid

# Links for included namespaces
NS_ERMS = "https://DILCIS.eu/XML/ERMS"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"

# Namespace dict with explicit prefix
NSMAP = {
    "erms": NS_ERMS,
    "xsi": NS_XSI
}

BASE_DIR = Path(__file__).resolve().parents[2]
KLASSA_PROCESSES_PATH = BASE_DIR / "config" / "klassa_processer.json"

with KLASSA_PROCESSES_PATH.open("r", encoding="utf-8") as f:
    KLASSA = json.load(f)


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(message)s")


def validate_root_path(root: Path) -> None:
    if not root.exists():
        raise FileNotFoundError(f"Root path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Root path is not a directory: {root}")


def create_root_erms_element() -> etree.Element:
    # Root element <erms:erms>
    erms = etree.Element(etree.QName(NS_ERMS, "erms"), nsmap=NSMAP)

    # Add schemaLocation
    erms.set(
        etree.QName(NS_XSI, "schemaLocation"),
        f"{NS_ERMS} ERMS.xsd"
    )

    control = etree.SubElement(erms, etree.QName(NS_ERMS, "control"))

    identification = etree.SubElement(control, etree.QName(NS_ERMS, "identification"))
    identification.text = "KLASSA-ERMS-export"

    information_class = etree.SubElement(control, etree.QName(NS_ERMS, "informationClass"))
    information_class.text = "ERMS export"

    return erms


def add_aggregations_container(erms_root: etree.Element) -> etree.Element:
    return etree.SubElement(erms_root, etree.QName(NS_ERMS, "aggregations"))


def create_aggregation_for_folder(parent: etree.Element, folder: Path) -> etree.Element:
    aggregation = etree.SubElement(parent, etree.QName(NS_ERMS, "aggregation"))

    aggregation.set("systemIdentifier", str(uuid.uuid4()))

    aggregation.set("aggregationType", "Class")

    object_id = etree.SubElement(aggregation, etree.QName(NS_ERMS, "objectID"))
    object_id.text = folder.name

    information_class = etree.SubElement(aggregation, etree.QName(NS_ERMS, "informationClass"))
    information_class.text = "1"

    if folder.name not in KLASSA:
        raise KeyError(f"Classification not found in json: {folder.name}")

    title = etree.SubElement(aggregation, etree.QName(NS_ERMS, "title"))

    # Dynamic attribution of title text based on KLASSA mapping
    title.text = KLASSA.get(folder.name, folder.name)

    classification = etree.SubElement(aggregation, etree.QName(NS_ERMS, "classification"))
    classification.text = folder.name

    records = etree.SubElement(aggregation, etree.QName(NS_ERMS, "records"))
    return records


def create_record_for_file(records_container: etree.Element, file_path: Path, output_path: Path) -> None:
    record = etree.SubElement(records_container, etree.QName(NS_ERMS, "record"))

    record.set("systemIdentifier", str(uuid.uuid4()))

    dates = etree.SubElement(record, etree.QName(NS_ERMS, "dates"))
    date = etree.SubElement(dates, etree.QName(NS_ERMS, "date"))
    date.set("dateType", "created")
    created_ts = file_path.stat().st_ctime
    date.text = datetime.datetime.fromtimestamp(created_ts).replace(microsecond=0).isoformat(timespec="seconds")

    object_id = etree.SubElement(record, etree.QName(NS_ERMS, "objectID"))
    object_id.text = file_path.name

    title = etree.SubElement(record, etree.QName(NS_ERMS, "title"))
    title.text = str(file_path.name)

    additionalInformation = etree.SubElement(record, etree.QName(NS_ERMS, "additionalInformation"))
    appendix = etree.SubElement(additionalInformation, etree.QName(NS_ERMS, "appendix"))
    relative = file_path.relative_to(output_path.parent)
    appendix.set("Path", str(relative))

def build_erms_from_folder_structure(root_path: Path, output_path: Path) -> etree.ElementTree:

    validate_root_path(root_path)

    erms_root = create_root_erms_element()
    processing_instruction = etree.ProcessingInstruction(
    "xml-model",
    'href="erms.sch" type="application/xml" schematypens="http://purl.oclc.org/dsdl/schematron"'
    )

    erms_root.addprevious(processing_instruction)

    aggregations = add_aggregations_container(erms_root)

    for child in sorted(root_path.iterdir()):
        if not child.is_dir():
            logging.debug("Ignoring non-directory at root: %s", child)
            continue

        logging.info("Processing folder as aggregation: %s", child)
        try:
            records_container = create_aggregation_for_folder(aggregations, child)
        except KeyError:
            logging.error("Skipping folder due to missing classification: %s", child)
            continue

        for item in sorted(child.iterdir()):
            if item.is_dir():
                logging.warning("Ignoring nested directory inside %s: %s", child, item)
                continue

            logging.info("Adding file as record: %s", item)
            create_record_for_file(records_container, item, output_path)


    return etree.ElementTree(erms_root)


def write_xml(tree: etree.ElementTree, output_path: Path) -> None:
    if output_path.exists() and output_path.is_dir():
        raise IsADirectoryError(f"Output path is a directory: {output_path}")

    if output_path.parent and not output_path.parent.exists():
        raise FileNotFoundError(f"Output directory does not exist: {output_path.parent}")

    logging.info("Writing XML to: %s", output_path)

    root = tree.getroot()

    pretty_xml = etree.tostring(
        tree,
        pretty_print=True,
        xml_declaration=True,
        encoding="utf-8"
    )

    with output_path.open("wb") as f:
        f.write(pretty_xml)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate CITS-ERMS 2.1.0 XML from a KLASSA-based folder structure."
    )
    parser.add_argument("root", type=str, help="Root folder containing KLASSA process folders.")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output XML file.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)

    try:
        root_path = Path(args.root)
        output_path = Path(args.output)

        tree = build_erms_from_folder_structure(root_path, output_path)
        write_xml(tree, output_path)

        logging.info("Done.")
        return 0
    except Exception as exc:
        logging.error("Failed to generate ERMS XML: %s", exc, exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
