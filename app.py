import streamlit as st
from pdf import *
from config import *


st.title("Research Paper Parser 📄")
st.write(
    "A program that takes in management academic research PDF files from certain journals, analyzes them, and outputs two CSV files. One CSV file should dissect the research papers into sections, and the other CSV file should provide all references within the paper and the sections in which they were used."
)
journal = st.selectbox(label="Select Journal", options=JOURNALS)

if journal == DEFAULT_OPTION:
    # Upload the file!
    st.write("Upload the PDF file to get started")
else:
    pdf_file = st.file_uploader("Upload the paper's PDF")
    st.write("---")
    st.header("Results")
    if pdf_file:
        pdf_file_contents = pdf_file.getvalue()
        doc = fitz.open("pdf", pdf_file_contents)
        sections_df, references_df = convert_pdf_to_dataframes(doc)

        st.header("Sections")
        sections_display = st.dataframe(sections_df)
        sections_download = st.download_button(
            label="Download",
            data=sections_df.to_csv(),
            file_name=f"{doc.name}_sections.csv",
        )
        st.header("References")
        references_display = st.dataframe(references_df)
        references_download = st.download_button(
            label="Download",
            data=references_df.to_csv(),
            file_name=f"{doc.name}_references.csv",
        )
