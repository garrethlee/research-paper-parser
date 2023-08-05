from journals import annurev, aom, asq, orgsci, jom, joap

JOURNALS = [
    "",
    "OrgSci",
    "Annurev-Orgpsych",
    "Academy of Management Journal (AOM)",
    "Administrative Science Quarterly (ASQ)",
    "Journal of Management",
    "Journal of Applied Psychology",
]

DEFAULT_OPTION, ORGSCI, ANNUREV_ORGPSYCH, AOM, ASQ, JOM, JOAP = JOURNALS

journal_map = {
    ORGSCI: orgsci.convert_pdf_to_dataframes,
    ANNUREV_ORGPSYCH: annurev.convert_pdf_to_dataframes,
    AOM: aom.convert_pdf_to_dataframes,
    ASQ: asq.convert_pdf_to_dataframes,
    JOM: jom.convert_pdf_to_dataframes,
    JOAP: joap.convert_pdf_to_dataframes,
}
