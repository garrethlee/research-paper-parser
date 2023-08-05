import sys
import traceback

import fitz
import streamlit as st
from loguru import logger
from journals import orgsci

from config import JOURNALS, DEFAULT_OPTION, journal_map

logger.add(sys.stdout, backtrace=True, diagnose=True)


def set_converted_state(state):
    """
    Set the converted state.

    Parameters:
        state (bool): The state to be set.

    Returns:
        None
    """
    if "convert_clicked" not in st.session_state:
        st.session_state["convert_clicked"] = False
    st.session_state["convert_clicked"] = state


st.title("Research Paper Parser 📄")
st.write(
    "A program that takes in management academic research PDF files from certain journals, analyzes them, and outputs two CSV files. One CSV file should dissect the research papers into sections, and the other CSV file should provide all references within the paper and the sections in which they were used."
)

with st.expander("Frequently Asked Questions ﹖"):
    st.write(
        """Q: Why do extracted data sometimes miss citations and contain errors?
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
    )


journal = st.selectbox(
    label="Select Journal",
    options=JOURNALS,
    on_change=set_converted_state,
    args=[False],
)

if journal == DEFAULT_OPTION:
    st.write("Upload the PDF file to get started")
else:
    col1, col2 = st.columns([5, 1])
    with col1:
        pdf_file = st.file_uploader(
            "Upload the paper's PDF", on_change=set_converted_state, args=[False]
        )
    with col2:
        # ADD PADDING
        st.text("")
        st.text("")
        st.text("")
        convert_button = st.button(
            "Convert",
            disabled=pdf_file is None,
            on_click=set_converted_state,
            args=[True],
        )
    st.write("---")
    st.header("Results")

    if st.session_state["convert_clicked"] and pdf_file:
        pdf_file_contents = pdf_file.getvalue()
        doc = fitz.open("pdf", pdf_file_contents)
        try:
            sections_df, references_df = journal_map[journal](doc)
            st.session_state.convert_success = True
        except Exception as e:
            NEWLINE = "\n\n"
            st.error(
                "Whoops! There seems to be an error. Did you make sure that the journal selected matches the file you uploaded?\n\n\n"
                + "============ \n\n\n"
                + f"Traceback: {NEWLINE.join(traceback.format_exception(e))}"
            )
            logger.error(f"Exception found: {e.with_traceback(e.__traceback__)}")
            st.session_state.convert_success = False

        if st.session_state.convert_success:
            st.header("Sections")
            sections_display = st.dataframe(sections_df)
            sections_download_button = st.download_button(
                label="Download",
                data=orgsci.sanitize_dataframe_for_download(sections_df).to_csv(),
                file_name=f"{doc.name}_sections.csv",
            )
            st.header("References")
            references_display = st.dataframe(references_df)
            references_download_button = st.download_button(
                label="Download",
                data=orgsci.sanitize_dataframe_for_download(references_df).to_csv(),
                file_name=f"{doc.name}_references.csv",
            )


st.markdown("---")
st.markdown("Made by [Garreth Lee](https://linkedin.com/in/garrethlee)")
