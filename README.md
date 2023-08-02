# Research Paper Parser 📄

This is a program that takes management academic research PDF files from certain journals, analyzes them, and outputs two CSV files. One CSV file dissects the research papers into sections, and the other CSV file provides all references within the paper and the sections in which they were used.

## Usage

1. Select the journal from the dropdown menu.
2. If the selected option is not a valid journal, it will prompt you to upload the PDF file.
3. If you select a valid journal, you can then upload the corresponding research paper's PDF.
4. Click the "Convert" button to initiate the analysis and extraction process.

## Frequently Asked Questions 🤔

Q: Why do extracted data sometimes miss citations and contain errors?

A: The PDF data extraction process may encounter challenges in recognizing and extracting citations. Citations can come in different formats (e.g., (Greve, 2003b), Greve (2003), (Greeve, 2003), (Greeve, 2003:134-135)), making it difficult for automated extraction methods to capture them accurately. Additionally, certain formatting styles, such as superscripts, may not be correctly interpreted and can be read as normal text, leading to inaccuracies.

Q: How does the inconsistency of PDF formats contribute to data extraction issues?

A: PDF documents can have varying layouts, fonts, and structures, which can cause inconsistencies during data extraction. These variations in formatting may result in errors or omissions in the extracted data.

Q: How can users validate the accuracy of the extracted data?

A: It is essential to verify the extracted data manually, especially when critical information, like citations or numerical data, is involved. Cross-referencing with the original PDF and performing sample checks can help identify and rectify potential errors.

Q: Are there any limitations to PDF data extraction tools?

A: Yes, PDF data extraction tools may have limitations in handling complex PDF layouts, scanned documents without text layers, or documents with embedded images. Users should be aware of these limitations when using PDF data extraction tools.

---

## Results

Once you have uploaded the PDF and clicked the "Convert" button, the results will be displayed below.

### Sections

This section will display the extracted sections from the research paper.

### References

This section will display all the references found within the paper and the sections in which they were used.

You can also download the extracted data as CSV files using the "Download" buttons provided for each section.

---

By Garreth Lee (2023)
