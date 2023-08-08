from journals import annurev, aom, asq, orgsci, jom, joap, personnel

APP_DESCRIPTION = (
    "A program that takes in management academic research PDF files"
    "from certain journals, analyzes them, and outputs two CSV files. "
    "One CSV file should dissect the research papers into sections, and "
    "the other CSV file should provide all references within the paper and "
    "the sections in which they were used."
)

FAQ = """Q: Why do extracted data sometimes miss citations and contain errors?
---
A: The PDF data extraction process may encounter challenges in recognizing and extracting citations. Citations can come in different formats (e.g., (Greve, 2003b), Greve (2003), (Greeve, 2003), (Greeve, 2003:134-135)), making it difficult for automated extraction methods to capture them accurately. Additionally, certain formatting styles, such as superscripts, may not be correctly interpreted and can be read as normal text, leading to inaccuracies.

Q: How does the inconsistency of PDF formats contribute to data extraction issues?
---
A: PDF documents can have varying layouts, fonts, and structures, which can cause inconsistencies during data extraction. These variations in formatting may result in errors or omissions in the extracted data.

Q: How can users validate the accuracy of the extracted data?
---
A: It is essential to verify the extracted data manually, especially when critical information, like citations or numerical data, is involved. Cross-referencing with the original PDF and performing sample checks can help identify and rectify potential errors.

Q: Are there any limitations to PDF data extraction tools?
---
A: Yes, PDF data extraction tools may have limitations in handling complex PDF layouts, scanned documents without text layers, or documents with embedded images. Users should be aware of these limitations when using PDF data extraction tools.
"""

JOURNALS = [
    "",
    "OrgSci",
    "Annurev-Orgpsych",
    "Academy of Management Journal (AOM)",
    "Administrative Science Quarterly (ASQ)",
    "Journal of Management",
    "Journal of Applied Psychology",
    "Personnel Psychology",
]

DEFAULT_OPTION, ORGSCI, ANNUREV_ORGPSYCH, AOM, ASQ, JOM, JOAP, PERSONNEL = JOURNALS

journal_map = {
    ORGSCI: orgsci.convert_pdf_to_dataframes,
    ANNUREV_ORGPSYCH: annurev.convert_pdf_to_dataframes,
    AOM: aom.convert_pdf_to_dataframes,
    ASQ: asq.convert_pdf_to_dataframes,
    JOM: jom.convert_pdf_to_dataframes,
    JOAP: joap.convert_pdf_to_dataframes,
    PERSONNEL: personnel.convert_pdf_to_dataframes,
}
