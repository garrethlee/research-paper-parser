import pandas as pd
from test_config import *
from config import *
import shutil
import os
import random
import fitz

underscore = "_"


def generate_pdf_samples():
    data_dir = "data"
    test_dir = os.path.join(data_dir, "tests", "pdf")
    journal_dirs = os.listdir(data_dir)

    for journal_dir in journal_dirs:
        # Skip the tests folder
        if journal_dir != "tests":
            data_path = os.path.join(data_dir, journal_dir)
            if os.path.isdir(data_path):
                pdf_files = os.listdir(data_path)
                if len(pdf_files) > 0:
                    # Get a pdf file
                    pdf_path = random.choice(pdf_files)
                    src_path = os.path.join(data_path, pdf_path)
                    dest_path = os.path.join(
                        test_dir, f"{journal_dir}_sample_paper.pdf"
                    )
                    shutil.copy(src=src_path, dst=dest_path)
                    print(f"Successfully created {dest_path}!")


def test_orgsci():
    journal = JOM
    sample_pdf_path = TEST_PATHS[journal]
    actual_csv_path = os.path.join("data", "tests", "csv")
    actual_sections_csv_path = os.path.join(
        actual_csv_path,
        f"{underscore.join([word.lower() for word in journal.split()])}_sample_paper_sections.csv",
    )
    actual_references_csv_path = os.path.join(
        actual_csv_path,
        f"{underscore.join([word.lower() for word in journal.split()])}_sample_paper_references.csv",
    )

    actual_section_df = pd.read_csv(
        actual_sections_csv_path, index_col=["Unnamed: 0"]
    ).fillna("")
    actual_references_df = (
        pd.read_csv(actual_references_csv_path).drop(["Unnamed: 0"], axis=1).fillna("")
    )

    # produce dataframes
    doc = fitz.open(sample_pdf_path)
    output_section_df, output_references_df = journal_map[journal](doc)

    output_section_df = orgsci.sanitize_dataframe_for_download(output_section_df)
    output_references_df = orgsci.sanitize_dataframe_for_download(output_references_df)

    print(actual_section_df, output_section_df)
    assert output_section_df.equals(actual_section_df)
    print(actual_references_df, output_references_df)
    assert output_references_df.equals(actual_references_df)
