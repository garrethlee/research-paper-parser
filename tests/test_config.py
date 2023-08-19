from config import *
import os
import pprint

test_pdf_dir = os.path.join("data", "tests", "pdf")

TEST_PATHS = {
    " ".join(
        [word.title() if word != "of" else word for word in pdf_file.split("_")[:-2]]
    ): os.path.join(test_pdf_dir, pdf_file)
    for pdf_file in os.listdir(test_pdf_dir)
}

print(TEST_PATHS)
