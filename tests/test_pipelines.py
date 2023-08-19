import pandas as pd
from test_config import *
from config import *
import shutil
import os
import fitz


def generate_pdf_samples():
    data_dir = "data"
    test_dir = os.path.join(data_dir, "tests")
    journal_dirs = os.listdir(data_dir)

    for journal_dir in journal_dirs:
        # Skip the tests folder
        if journal_dir != "tests":
            data_path = os.path.join(data_dir, journal_dir)
            if os.path.isdir(data_path):
                pdf_files = os.listdir(data_path)
                if len(pdf_files) > 0:
                    # Get a pdf file
                    pdf_path = pdf_files[0]
                    src_path = os.path.join(data_path, pdf_path)
                    dest_path = os.path.join(
                        test_dir, f"{journal_dir}_sample_paper.pdf"
                    )
                    shutil.copy(src=src_path, dst=dest_path)
                    print(f"Successfully created {dest_path}!")


def test_orgsci():
    sample_pdf_path = TEST_PATHS[ORGSCI]
    print(sample_pdf_path)

    actual_section_df = pd.read_csv()
    actual_references_df = pd.read_csv()

    # produce doc
    doc = fitz.open()
    output_section_df, output_references_df = journal_map[ORGSCI]()

    assert output_section_df.equals(actual_section_df)
    assert output_references_df.equals(actual_references_df)
