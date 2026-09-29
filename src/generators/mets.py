"""
Generate a METS file with minimum requirements according to the CSIP profile.
"""

import datetime
import sys
import logging
import hashlib
import mimetypes
import uuid
from lxml import etree
from pathlib import Path
from src.common.utils import (
    parse_args,
    setup_logging,
    determine_project_root,
    validate_root_path,
    load_run_config,
    load_submission_agreement,
    write_xml
)

# Links for included namespaces
NS_METS = "http://www.loc.gov/METS/"
NS_XLINK = "http://www.w3.org/1999/xlink"
NS_CSIP = "https://DILCIS.eu/XML/METS/CSIPExtensionMETS"
NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"


NSMAP = {
    "mets": NS_METS,
    "xsi": NS_XSI,
    "xlink": NS_XLINK,
    "csip": NS_CSIP
}


def create_root_mets_element(submission) -> etree.Element:
    """
    Adds the root element <mets> with its attributes and an xml-declaration.
    """

    logging.info("Starting the creation of mets.xml")

    mets = etree.Element(etree.QName(NS_METS, "mets"), nsmap=NSMAP)

    mets.set(etree.QName("OBJID"), f"IP_" + str(uuid.uuid4()))
    mets.set(etree.QName("LABEL"), submission.get("label", ""))
    mets.set(etree.QName("TYPE"), f"OTHER")
    mets.set(etree.QName(NS_CSIP, "OTHERTYPE"), submission.get("other_type", ""))
    mets.set(etree.QName("PROFILE"), submission.get("profile", ""))
    mets.set(
        etree.QName(NS_XSI, "schemaLocation"),
        f"{NS_METS} schemas/mets.xsd {NS_XLINK} schemas/xlink.xsd {NS_CSIP} schemas/DILCISExtensionMETS.xsd"
    )

    logging.debug(
        "Created root <erms> element with namespaces, schema locations and other mandatory attributes.")
    return mets


def create_metsHdr_element(mets_root: etree.Element, submission) -> etree.Element:
    """
    Creates the header element with the agents involved in the submission.
    This version has expanded on the minimun required agents.
    In total it uses:
    1. the organization that created the archive
    2. the system where the archive was originally kept
    3. the organization that has the continued responsibility for preservation functions
    4. software used for the creation of the SIP (this program)
    5. the organization responsible for the creation of the SIP
    6. the individiual responsible for the creation of the SIP
    """

    metsHdr = etree.SubElement(mets_root, etree.QName(NS_METS, "metsHdr"))

    metsHdr.set(etree.QName("CREATEDATE"), datetime.datetime.now().replace(
        microsecond=0).isoformat(timespec="seconds"))
    metsHdr.set(etree.QName("RECORDSTATUS"), submission.get("recordstatus", ""))
    metsHdr.set(etree.QName(NS_CSIP, "OAISPACKAGETYPE"), "SIP")

    # The organization where the archive was created
    agent_archivist = etree.SubElement(metsHdr, etree.QName(NS_METS, "agent"))
    agent_archivist.set(etree.QName("ROLE"), "ARCHIVIST")
    agent_archivist.set(etree.QName("TYPE"), "ORGANIZATION")
    agent_archivist_name = etree.SubElement(agent_archivist, etree.QName(NS_METS, "name"))
    agent_archivist_name.text = submission.get("archivist", "")
    agent_archivist_note = etree.SubElement(agent_archivist, etree.QName(NS_METS, "note"))
    agent_archivist_note.text = submission.get("archivist_org", "")

    # The system where the archive was kept
    agent_system = etree.SubElement(metsHdr, etree.QName(NS_METS, "agent"))
    agent_system.set(etree.QName("ROLE"), "ARCHIVIST")
    agent_system.set(etree.QName("TYPE"), "OTHER")
    agent_system.set(etree.QName("OTHERTYPE"), "SOFTWARE")
    agent_system_name = etree.SubElement(agent_system, etree.QName(NS_METS, "name"))
    agent_system_name.text = submission.get("system", "")
    agent_system_note = etree.SubElement(agent_system, etree.QName(NS_METS, "note"))
    agent_system_note.set(etree.QName(NS_CSIP, "NOTETYPE"), "SOFTWARE VERSION")
    agent_system_note.text = submission.get("system_note", "")

    # The organization with continued responsibility for preservation
    agent_preservation = etree.SubElement(metsHdr, etree.QName(NS_METS, "agent"))
    agent_preservation.set(etree.QName("ROLE"), "PRESERVATION")
    agent_preservation.set(etree.QName("TYPE"), "ORGANIZATION")
    agent_preservation_name = etree.SubElement(agent_preservation, etree.QName(NS_METS, "name"))
    agent_preservation_name.text = submission.get("preservation", "")

    # The software used for the creation of the SIP
    agent_software = etree.SubElement(metsHdr, etree.QName(NS_METS, "agent"))
    agent_software.set(etree.QName("ROLE"), "CREATOR")
    agent_software.set(etree.QName("TYPE"), "OTHER")
    agent_software.set(etree.QName("OTHERTYPE"), "SOFTWARE")
    agent_software_name = etree.SubElement(agent_software, etree.QName(NS_METS, "name"))
    agent_software_name.text = submission.get("sip_creator", "")
    agent_software_note = etree.SubElement(agent_software, etree.QName(NS_METS, "note"))
    agent_software_note.set(etree.QName(NS_CSIP, "NOTETYPE"), "SOFTWARE VERSION")
    agent_software_note.text = submission.get("sip_creator_note", "")

    # The organization responsible for the creation of the SIP
    agent_creator_organization = etree.SubElement(metsHdr, etree.QName(NS_METS, "agent"))
    agent_creator_organization.set(etree.QName("ROLE"), "CREATOR")
    agent_creator_organization.set(etree.QName("TYPE"), "ORGANIZATION")
    agent_creator_organization_name = etree.SubElement(
        agent_creator_organization, etree.QName(NS_METS, "name"))
    agent_creator_organization_name.text = submission.get("creator_organization", "")

    # The individual at the organization responsible for the creation of the sip
    agent_creator_individual = etree.SubElement(metsHdr, etree.QName(NS_METS, "agent"))
    agent_creator_individual.set(etree.QName("ROLE"), "CREATOR")
    agent_creator_individual.set(etree.QName("TYPE"), "INDIVIDUAL")
    agent_creator_individual_name = etree.SubElement(
        agent_creator_individual, etree.QName(NS_METS, "name"))
    agent_creator_individual_name.text = submission.get("creator_individual", "")
    agent_creator_individual_note = etree.SubElement(
        agent_creator_individual, etree.QName(NS_METS, "note"))
    agent_creator_individual_note.text = submission.get("creator_individual_contact", "")

    submission_agreement_id = etree.SubElement(metsHdr, etree.QName(NS_METS, "altRecordID"))
    submission_agreement_id.set(etree.QName("TYPE"), "SUBMISSIONAGREEMENT")
    submission_agreement_id.text = submission.get("submission_agreement", "")

    logging.debug("Created <metsHdr> element and children.")
    return metsHdr


def add_filesec_section(mets_root: etree.Element) -> etree.Element:
    """
    Adds the <mets:fileSec> container to the root <mets:mets> element.
    """
    logging.debug("Created <mets:fileSec element.")
    fileSec = etree.SubElement(mets_root, etree.QName(NS_METS, "fileSec"))
    # There can only ever be one fileSec element, and no other element uses anything but an UUID as its ID, hence the ID being hardcoded like this
    fileSec.set(etree.QName("ID"), "ID001")

    return fileSec


def add_fileGrps(mets_fileSec: etree.Element, sip_root: Path) -> list[etree.Element]:
    """
    Adds fileGrp element for each subfolder to SIP that contains at least one file directly under itself or in one of its subfolders.
    Note that technically, 'schemas' and 'representations' are required as a minimun in CSIP
    """

    # Stores the fileGrps that are created in a list by appending them in the for loop below
    created_fileGrps = []

    # Based on the CSIP specification. If more subfolders should be added, they must be included here
    valid_subfolders = ["schemas", "representations", "metadata", "documentation"]

    for folder in valid_subfolders:
        folder_path = sip_root / folder
        if not folder_path.exists() or not folder_path.is_dir():
            continue

        # Search recursively through the folder and its subfolders in case there are any files at any level
        contains_files = any(p.is_file() for p in folder_path.rglob("*"))

        # Skip if there are no files
        if not contains_files:
            continue

        fileGrp = etree.SubElement(mets_fileSec, etree.QName(NS_METS, "fileGrp"))

        fileGrp.set("ID", "ID" + str(uuid.uuid4()))

        # The value for USE is always capitalized, in case the folder names are in all lower case.
        # The CSIP spec is not consistent in the naming scheme for subfolders to SIP, allowing both lowercase and capitalized versions. The value for USE is however clear in that it should be capitalized.
        fileGrp.set("USE", folder.capitalize())

        created_fileGrps.append(fileGrp)

    return created_fileGrps


def sha256_checksum(path: Path) -> str:
    """
    Calculates a checksum for a file using SHA-256 as a method.
    Confirmed to generate valid checksums through checking generated checksum with that of another program for the same file
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def add_files_to_fileGrp(fileGrp: etree.Element, folder_path: Path, sip_root: Path):
    """
    Adds file elements for each file belonging to each fileGrp.
    Uses minimal requirements.
    """

    added_files = []

    for file_path in folder_path.rglob("*"):
        if not file_path.is_file():
            continue

        file_element = etree.SubElement(fileGrp, etree.QName(NS_METS, "file"))
        file_element.set("ID", "ID" + str(uuid.uuid4()))

        # Only checks the file extension, if the functions cannot guess the mimetype it gives a placeholder value
        mimetype, _ = mimetypes.guess_type(file_path.name)
        file_element.set("MIMETYPE", mimetype or "application/octet-stream")

        checksum = sha256_checksum(file_path)
        file_element.set("CHECKSUM", checksum)
        file_element.set("CHECKSUMTYPE", "SHA-256")

        # Gives the size value in bytes
        file_element.set("SIZE", str(file_path.stat().st_size))

        file_element.set(
            "CREATED",
            datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
            .replace(microsecond=0)
            .isoformat(timespec="seconds")
        )

        flocat = etree.SubElement(file_element, etree.QName(NS_METS, "FLocat"))
        flocat.set("LOCTYPE", "URL")

        relative_path = file_path.relative_to(sip_root)
        flocat.set(etree.QName(NS_XLINK, "type"), "simple")

        # Versions of FGS paketstruktur have had a requirement of the prefix "file:///", but is no longer there in CSIP. Can easily be added before the string of the relative path by concatenation if needed.
        flocat.set(etree.QName(NS_XLINK, "href"), str(relative_path).replace("\\", "/"))

        added_files.append(file_element)

    return added_files


def add_structMap_csip(mets_root, folders):
    """
    Adds divs for each fileGrp included in the SIP according to the minimum requirements in CSIP.
    """
    structMap = etree.SubElement(mets_root, etree.QName(NS_METS, "structMap"))
    structMap.set("ID", "csip-structmap")
    structMap.set("TYPE", "PHYSICAL")
    structMap.set("LABEL", "CSIP")

    root_div = etree.SubElement(structMap, etree.QName(NS_METS, "div"))
    root_div.set("ID", "csip-mets-div")
    root_div.set("LABEL", "csip-mets")

    for folder_name, fileGrp_id in folders.items():
        div = etree.SubElement(root_div, etree.QName(NS_METS, "div"))
        div.set("ID", f"div-{folder_name}")
        div.set("LABEL", folder_name)

        fptr = etree.SubElement(div, etree.QName(NS_METS, "fptr"))
        fptr.set("FILEID", fileGrp_id)

    return structMap


def build_mets_from_folder_structure(sip_root, submission):
    """
    Calls each function that creates a section of the mets.xml-file.
    """
    validate_root_path(sip_root)
    mets_root = create_root_mets_element(submission)
    create_metsHdr_element(mets_root, submission)
    fileSec = add_filesec_section(mets_root)
    fileGrps = add_fileGrps(fileSec, sip_root)

    folder_to_fileGrpID = {}

    for fileGrp in fileGrps:
        folder_name = fileGrp.get("USE").lower()
        fileGrp_id = fileGrp.get("ID")
        folder_to_fileGrpID[folder_name] = fileGrp_id
        folder_path = sip_root / folder_name
        add_files_to_fileGrp(fileGrp, folder_path=folder_path, sip_root=sip_root)

    add_structMap_csip(mets_root, folder_to_fileGrpID)

    return etree.ElementTree(mets_root)


def main(argv=None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)

    # Starts the clock for runtime after all initial checks have been cleared
    start_time = datetime.datetime.now()

    try:
        project_root = determine_project_root()
        run_config = load_run_config(project_root)
        submission = load_submission_agreement(project_root)

        # Uses the config path if there are no command-line arguments
        # Path to which folders, subfolders and files the program should go through.
        sip_root = Path(args.root) if args.root else Path(run_config["sip_root"])

        # The path MUST always be this for the CSIP structure
        # Path for where to save the XML-file that the program produces.
        output_path = Path(args.output) if args.output else sip_root / "mets.xml"

        # Build the xml-structure
        tree = build_mets_from_folder_structure(
            sip_root=sip_root,
            submission=submission
        )

        # Create the xml-file
        write_xml(tree, output_path)

        # Stops the clock for runtime
        elapsed = datetime.datetime.now() - start_time

        # If nothing went wrong, tell the user that the program is done running and how long it took to run
        logging.info(
            "Done. The program %s took %.2f seconds to run", Path(__file__).name, elapsed.total_seconds()
        )
        return 0

    except Exception as exc:
        logging.error("Failed to generate METS XML: %s", exc, exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
