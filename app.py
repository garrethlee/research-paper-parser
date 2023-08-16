import sys
import traceback

import fitz
import streamlit as st
from loguru import logger

from config import *
from journals import orgsci

logger.add(sys.stdout, backtrace=True, diagnose=True)


def save_editor_changes():
    pdf_dataframe = st.session_state["pdf_dataframe"]
    updates = st.session_state["pdf_editor"]["edited_rows"]
    # Save the updated dataframe in the session state
    for idx, journal_dict in updates.items():
        for key in journal_dict:
            journal = journal_dict[key]
        pdf_dataframe.at[idx, "Journal"] = journal

    pdf_to_journal_records = pdf_dataframe.to_dict(orient="records")
    # Update the session state's pdf-to-journal matches
    for record in pdf_to_journal_records:
        filename, journal = list(record.values())
        st.session_state["pdf_to_journal_map"][filename] = journal


def create_pdf_dataframe(pdf_files):
    import pandas as pd
    if "pdf_to_journal_map" not in st.session_state:
        st.session_state["pdf_to_journal_map"] = {}

    pdf_file_names = []
    journals = []

    # Check session state for any available values
    for pdf_file in pdf_files:
        filename = pdf_file.name
        journal = st.session_state["pdf_to_journal_map"].get(filename, None)

        pdf_file_names.append(filename)
        journals.append(journal)

    pdf_dataframe = pd.DataFrame(
        {"Filename": pdf_file_names, "Journal": journals})

    # Save current dataframe in session state
    st.session_state['pdf_dataframe'] = pdf_dataframe

    return pdf_dataframe


st.title("Research Paper Parser 📄")
st.write(APP_DESCRIPTION)

with st.expander("Frequently Asked Questions ﹖"):
    st.write(FAQ)


pdf_files = st.file_uploader(
    "Upload the paper's PDF", accept_multiple_files=True
)

uploaded_pdf_dataframe = create_pdf_dataframe(pdf_files)
uploaded_pdf_editor = st.data_editor(
    uploaded_pdf_dataframe,
    column_config={
        "Filename": st.column_config.Column(
            "Filename",
            help="Name of PDF file",
            disabled=True,
        ),
        "Journal": st.column_config.SelectboxColumn(
            "Journal",
            help="The journal the article belongs to",
            required=True,
            width="large",
            options=JOURNALS
        )
    }, key="pdf_editor", hide_index=True, on_change=save_editor_changes)


convert_button = st.button(
    "⚙️ Convert",
    disabled=(not all(uploaded_pdf_editor.get(
        "Journal", [None]))) or len(pdf_files) == 0,

)

st.write("---")
st.header("Results")

if convert_button:
    pdf_file_contents = pdf_files.getvalue()
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
        logger.error(
            f"Exception found: {e.with_traceback(e.__traceback__)}")

    if st.session_state.convert_success:
        st.header("Sections")
        sections_display = st.dataframe(sections_df)
        sections_download_button = st.download_button(
            label="Download",
            data=orgsci.sanitize_dataframe_for_download(
                sections_df).to_csv(),
            file_name=f"{doc.name}_sections.csv",
        )
        st.header("References")
        references_display = st.dataframe(references_df)
        references_download_button = st.download_button(
            label="Download",
            data=orgsci.sanitize_dataframe_for_download(
                references_df).to_csv(),
            file_name=f"{doc.name}_references.csv",
        )


st.markdown("---")
st.markdown("Made by [Garreth Lee](https://linkedin.com/in/garrethlee)")
