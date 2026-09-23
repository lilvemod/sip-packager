from lxml import etree
from pathlib import Path

NS_ERMS = "https://DILCIS.eu/XML/ERMS"

nsmap = {"erms": NS_ERMS}

root = etree.Element(etree.QName(NS_ERMS, "erms"), nsmap=nsmap)
child = etree.SubElement(root, etree.QName(NS_ERMS, "control"))

# Serialisera XML med pretty print
xml_bytes = etree.tostring(
    root,
    pretty_print=True,
    xml_declaration=True,
    encoding="utf-8"
)

# Skriv till fil
output_path = Path("C:\\Users\\marti\\OneDrive\\Dokument\\test_output.xml")
with output_path.open("wb") as f:
    f.write(xml_bytes)

print(f"XML sparad till {output_path.resolve()}")
