"""
Generate a CITS-ERMS 2.1.0 XML-file from a KLASSA 2.1-based folder structure.
"""

import datetime
import logging
import sys
import uuid
from lxml import etree
from pathlib import Path
from src.common.utils import (
    parse_args,
    setup_logging,
    determine_project_root,
    validate_root_path,
    load_run_config,
    load_klassa_processer,
    load_submission_agreement,
    write_xml
)

# Links for included namespaces
NS_ERMS = "https://DILCIS.eu/XML/ERMS"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
NS_SCHEMATRON = "http://purl.oclc.org/dsdl/schematron"

# Namespace dict with explicit prefix
NSMAP = {
    "erms": NS_ERMS,
    "xsi": NS_XSI
}


def create_root_erms_element() -> etree.Element:
    """
    Adds the root element <erms> and xml-declaration and schematron-declaration.
    """

    logging.info("Starting the creation of cits-erms.xml")

    erms = etree.Element(etree.QName(NS_ERMS, "erms"), nsmap=NSMAP)

    erms.set(
        etree.QName(NS_XSI, "schemaLocation"),
        f"{NS_ERMS} ../schemas/ERMS.xsd"
    )

    processing_instruction = etree.ProcessingInstruction(
        "xml-model",
        f'href="../schemas/erms.sch" type="application/xml" schematypens="{NS_SCHEMATRON}"'
    )

    erms.addprevious(processing_instruction)

    logging.debug("Created root <erms> element with namespaces and schema locations.")
    return erms


def create_control_element(erms_root, submission):
    """
    Creates the control element using a minimal profile of required metadata to validate against the CITS-ERMS schema.
    """

    control = etree.SubElement(erms_root, etree.QName(NS_ERMS, "control"))

    identification = etree.SubElement(control, etree.QName(NS_ERMS, "identification"))
    identification.set("identificationType", "UUID")
    identification.text = "uuid-" + str(uuid.uuid4())

    information_class = etree.SubElement(control, etree.QName(NS_ERMS, "informationClass"))
    information_class.text = submission.get("information_class", "")

    # Classificationschema should be adapted to local schemas when necessary and more <p> elements can be added to signal which specifici retention plan is used for the information included in the delivery.
    classificationSchema = etree.SubElement(control, etree.QName(NS_ERMS, "classificationSchema"))
    textualdescription = etree.SubElement(classificationSchema, etree.QName(
        NS_ERMS, "textualDescriptionOfClassificationSchema"))
    textualdescription_p = etree.SubElement(textualdescription, etree.QName(NS_ERMS, "p"))
    textualdescription_p.text = submission.get("classification_schema", "")

    maintenanceInformation = etree.SubElement(
        control, etree.QName(NS_ERMS, "maintenanceInformation"))
    maintenanceStatus = etree.SubElement(
        maintenanceInformation, etree.QName(NS_ERMS, "maintenanceStatus"))
    maintenanceStatus.set("value", "new")

    maintenanceAgency = etree.SubElement(
        maintenanceInformation, etree.QName(NS_ERMS, "maintenanceAgency"))
    agencyName = etree.SubElement(maintenanceAgency, etree.QName(NS_ERMS, "agencyName"))
    agencyName.text = submission.get("creator_organization", "")

    maintenanceHistory = etree.SubElement(
        maintenanceInformation, etree.QName(NS_ERMS, "maintenanceHistory"))
    maintenanceEvent = etree.SubElement(
        maintenanceHistory, etree.QName(NS_ERMS, "maintenanceEvent"))
    maintenanceEventType = etree.SubElement(maintenanceEvent, etree.QName(NS_ERMS, "eventType"))
    maintenanceEventType.set("value", "created")
    eventDateTime = etree.SubElement(maintenanceEvent, etree.QName(NS_ERMS, "eventDateTime"))
    eventDateTime.text = datetime.datetime.now().replace(microsecond=0).isoformat(timespec="seconds")

    maintenanceAgent = etree.SubElement(maintenanceEvent, etree.QName(NS_ERMS, "agent"))
    maintenanceAgent.set("agentType", "creator")
    maintenanceAgentName = etree.SubElement(maintenanceAgent, etree.QName(NS_ERMS, "name"))
    maintenanceAgentName.text = submission.get("creator_individual", "")

    logging.debug("Created <control> element and children.")
    return control


def add_aggregations_container(erms_root: etree.Element) -> etree.Element:
    """
    Adds the <erms:aggregations> container to the root <erms:erms> element.
    """
    logging.debug("Created <aggregations> element.")
    return etree.SubElement(erms_root, etree.QName(NS_ERMS, "aggregations"))


def create_class_aggregation_for_folder(parent, folder, klassa, submission):
    """
    Creates an aggregation element for each folder under the given path. Uses a minimal profile of required metadata to validate against the CITS-ERMS schema.
    """
    aggregation = etree.SubElement(parent, etree.QName(NS_ERMS, "aggregation"))

    aggregation.set("systemIdentifier", "UUID:" + str(uuid.uuid4()))

    aggregation.set("aggregationType", "class")

    object_id = etree.SubElement(aggregation, etree.QName(NS_ERMS, "objectId"))
    object_id.text = folder.name

    # Currently takes input value from submission agreement but should realistically be based on the classification of the information for the specific process, not the package as a whole.
    information_class = etree.SubElement(aggregation, etree.QName(NS_ERMS, "informationClass"))
    information_class.text = submission.get("information_class", "")

    classification = etree.SubElement(aggregation, etree.QName(NS_ERMS, "classification"))
    classification.text = folder.name

    if folder.name not in klassa:
        raise KeyError(f"Classification not found in json: {folder.name}")

    # Dynamic attribution of title text as name of process based on KLASSA mapping
    title = etree.SubElement(aggregation, etree.QName(NS_ERMS, "title"))
    title.text = klassa.get(folder.name, folder.name)

    logging.debug("Created <aggregation> element for folder: %s", folder)
    return aggregation

def create_casefile_aggregation_for_folder(parent, folder, submission):
    """
    Creates an aggregation element for each folder found within a class folder.
    """

    aggregation_casefile = etree.SubElement(parent, etree.QName(NS_ERMS, "aggregation"))
    aggregation_casefile.set("systemIdentifier", "UUID:" + str(uuid.uuid4()))
    aggregation_casefile.set("aggregationType", "caseFile")
    object_id = etree.SubElement(aggregation_casefile, etree.QName(NS_ERMS, "objectId"))
    object_id.text = f"{folder.parent.name}/{folder.name}"

    title_casefile = etree.SubElement(aggregation_casefile, etree.QName(NS_ERMS, "title"))
    title_casefile.text = folder.name

    logging.debug("Created <aggregation> element for case file folder: %s", folder)
    return aggregation_casefile


def create_record_for_file(records_container, file_path, output_path, klassa, submission, classification_code) -> None:
    """
    Creates a record element for each file directly under the aggregation folder. Uses a minimal profile of required metadata to validate against the CITS-ERMS schema.
    """
    record = etree.SubElement(records_container, etree.QName(NS_ERMS, "record"))
    record.set("systemIdentifier", "UUID:" + str(uuid.uuid4()))

    object_id = etree.SubElement(record, etree.QName(NS_ERMS, "objectId"))
    object_id.text = "uuid-" + str(uuid.uuid4())

    classification = etree.SubElement(record, etree.QName(NS_ERMS, "classification"))
    classification.text = (
        f"{classification_code} "
        f"{klassa.get(classification_code, classification_code)}"
    )

    file_name = str(file_path.name)
    clean_file_name = file_name.replace("_sekretess", "").replace("_signerad", "").replace("_", "")


    title = etree.SubElement(record, etree.QName(NS_ERMS, "title"))
    title.text = clean_file_name

    if "_sekretess" in file_name:
        restriction = etree.SubElement(record, etree.QName(NS_ERMS, "restriction"))
        restriction.set("restrictionType", "other_type")
        restriction.set("otherRestrictionType", "secrecy")
        regulation = etree.SubElement(restriction, etree.QName(NS_ERMS, "regulation"))
        regulation.text = "OSL, paragraf ej angiven"

    dates = etree.SubElement(record, etree.QName(NS_ERMS, "dates"))
    date = etree.SubElement(dates, etree.QName(NS_ERMS, "date"))
    date.set("dateType", "created")
    created_ts = file_path.stat().st_ctime
    date.text = datetime.datetime.fromtimestamp(created_ts).replace(
        microsecond=0).isoformat(timespec="seconds")

    additionalInformation = etree.SubElement(record, etree.QName(NS_ERMS, "additionalInformation"))
    appendix = etree.SubElement(additionalInformation, etree.QName(NS_ERMS, "appendix"))
    appendix.set("name", file_path.name)
    relative = file_path.relative_to(output_path.parent)
    appendix.set("path", str(relative))
    if "_signerad" in file_name:
        eSignature = etree.SubElement(appendix, etree.QName(NS_ERMS, "eSignature"))
        eSignature.set("present", "true")

    logging.debug("Created <record> element for file: %s", file_path)


def build_erms_from_folder_structure(root_path, output_path, klassa, submission):

    validate_root_path(root_path)
    erms_root = create_root_erms_element()
    create_control_element(erms_root, submission)
    aggregations = add_aggregations_container(erms_root)

    # Skips loose files at root
    for child in sorted(root_path.iterdir()):
        if not child.is_dir():
            logging.debug("Ignoring non-directory at root: %s", child)
            continue

        # Calls the function to create the class aggregations for each folder under root
        parent_aggregation = create_class_aggregation_for_folder(
            aggregations,
            child,
            klassa,
            submission
        )

        classification_code = child.name

        # Creates records belonging to the class aggregation
        for item in sorted(child.iterdir()):
            if item.is_file():
                create_record_for_file(
                    parent_aggregation,
                    item,
                    output_path,
                    klassa,
                    submission,
                    classification_code=classification_code
                )
            # Creates a casfile aggregation for each folder found within a class folder
            elif item.is_dir():
                child_aggregation = create_casefile_aggregation_for_folder(
                    parent_aggregation,
                    item,
                    submission
                )
                # Creates records belonging to the casefile aggregation
                for subitem in sorted(item.iterdir()):
                    if subitem.is_file():
                        create_record_for_file(
                            child_aggregation,
                            subitem,
                            output_path,
                            klassa,
                            submission,
                            classification_code=classification_code
                        )
                    # If another folder is found within the casefile aggregation, it will be ignored and logged as such.
                    else:
                        logging.debug(
                            "Ignoring directory %s, below supported depth of structure",
                            subitem
                        )

    return etree.ElementTree(erms_root)


def main(argv=None) -> int:
    start_time = datetime.datetime.now()

    args = parse_args(argv)
    setup_logging(args.verbose)

    try:
        project_root = determine_project_root()
        run_config = load_run_config(project_root)
        klassa = load_klassa_processer(project_root)
        submission = load_submission_agreement(project_root)

        # Uses the config path if there are no command-line arguments
        # Root folder containing KLASSA process folders.
        sip_root = Path(args.root) if args.root else Path(run_config["sip_root"])

        # The path *should* always be this if csip_structure has been used. However, there could be more than one "rep_xxx" sub-folder.
        # Borders on "magic number" and might have to be changed along the line to be its own key in run_config.json
        erms_input = sip_root / "representations" / "rep_001"

        # Where to save the XML file the program produces
        # Again, the name of the output file *might* have to be moved to run_config.json rather than being hardcoded here
        output_path = Path(args.output) if args.output else sip_root / \
            "representations" / "erms.xml"

        tree = build_erms_from_folder_structure(
            erms_input,
            output_path,
            klassa=klassa,
            submission=submission
        )

        write_xml(tree, output_path)

        elapsed = datetime.datetime.now() - start_time
        logging.info(
            "Done. The program %s took %.2f seconds to run", Path(__file__).name, elapsed.total_seconds()
        )
        return 0

    except Exception as exc:
        logging.error("Failed to generate ERMS XML: %s", exc, exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
