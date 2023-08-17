from zipfile import ZipFile
import io
import sys
import traceback

import fitz
import streamlit as st
from loguru import logger

from config import *
from helpers import *
from journals import orgsci

logger.add(sys.stdout, backtrace=True, diagnose=True)

if "convert_clicked" not in st.session_state:
    st.session_state["convert_clicked"] = False


st.title("Research Paper Parser 📄")
st.write(APP_DESCRIPTION)

with st.expander("Frequently Asked Questions ﹖"):
    st.write(FAQ)


pdf_files = st.file_uploader(
    "Upload the paper's PDF", accept_multiple_files=True, on_change=set_converted_state, args=(False,)
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
    on_click=set_converted_state, args=(True,)

)

st.write("---")
st.header("Results")


# Open zip file
zip_buffer = io.BytesIO()
pdf_file_zip = ZipFile(zip_buffer, "w")

# Show results if either:
#   1. convert button is clicked
#   2. no new files are uploaded
if convert_button or st.session_state["convert_clicked"]:
    uploaded_pdfs = uploaded_pdf_editor.to_dict(orient="records")
    for pdf_info, pdf_file in zip(uploaded_pdfs, pdf_files):
        journal = pdf_info['Journal']
        pdf_file_contents = pdf_file.getvalue()
        doc = fitz.open("pdf", pdf_file_contents)
        try:
            sections_df, references_df = journal_map[journal](doc)

            # Add created_files to zip
            with pdf_file_zip.open(f"{pdf_file.name[:-4]}_sections.csv", "w") as sections_csv:
                orgsci.sanitize_dataframe_for_download(
                    sections_df).to_csv(sections_csv)
            with pdf_file_zip.open(f"{pdf_file.name[:-4]}_references.csv", "w") as references_csv:
                orgsci.sanitize_dataframe_for_download(
                    references_df).to_csv(references_csv)

            # Success in expander
            with st.expander(f"✅{pdf_file.name}"):

                st.subheader("Sections")

                sections_display = st.dataframe(sections_df)
                sections_download_button = st.download_button(
                    label="Download",
                    data=orgsci.sanitize_dataframe_for_download(
                        sections_df).to_csv(),
                    file_name=f"{doc.name}_sections.csv",
                )

                st.subheader("References")
                references_display = st.dataframe(references_df)
                references_download_button = st.download_button(
                    label="Download",
                    data=orgsci.sanitize_dataframe_for_download(
                        references_df).to_csv(),
                    file_name=f"{doc.name}_references.csv",
                )

        except Exception as e:
            # Error in expander
            with st.expander(f"⚠️{pdf_file.name}"):
                NEWLINE = "\n\n"
                st.error(
                    "Whoops! There seems to be an error. Did you make sure that the journal selected matches the file you uploaded?\n\n\n"
                    + "============ \n\n\n"
                    + f"Traceback: {NEWLINE.join(traceback.format_exception(e))}"
                )
                logger.error(
                    f"Exception found: {e.with_traceback(e.__traceback__)}")

# Close the zip file
pdf_file_zip.close()

download_all_button = st.download_button(
    "Download All", data=zip_buffer.getvalue(), file_name="paper-sense-results.zip", mime="application/zip")


st.markdown("---")
st.markdown("Made by [Garreth Lee](https://linkedin.com/in/garrethlee)")
