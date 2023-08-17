from journals import annurev, aom, asq, orgsci, jom, joap, personnel

APP_DESCRIPTION = (
    "A program that takes in management academic research PDF files "
    "from certain journals, analyzes them, and outputs two CSV files. "
    "One CSV file should dissect the research papers into sections, and "
    "the other CSV file should provide all references within the paper and "
    "the sections in which they were used."
)

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

NEWLINE = "\n"

FAQ = f"""Q: Which papers are supported?
---
{f"{NEWLINE}- ".join(JOURNALS)}

Q: Why do extracted data sometimes miss citations and contain errors?
---
The PDF data extraction process may encounter challenges in recognizing and extracting citations. Citations can come in different formats (e.g., (Greve, 2003b), Greve (2003), (Greeve, 2003), (Greeve, 2003:134-135)), making it difficult for automated extraction methods to capture them accurately. Additionally, certain formatting styles, such as superscripts, may not be correctly interpreted and can be read as normal text, leading to inaccuracies.

Q: How does the inconsistency of PDF formats contribute to data extraction issues?
---
PDF documents can have varying layouts, fonts, and structures, which can cause inconsistencies during data extraction. These variations in formatting may result in errors or omissions in the extracted data.
"""

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
