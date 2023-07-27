import re
import traceback

import fitz
import pandas as pd
from loguru import logger

from section import *


def get_sections(doc):
    """
    Generates the sections for the given document.

    Parameters:
        doc (list): A list of pages in the document.

    Returns:
        list: The final sections of the document.
    """
    try:
        main_section = Section("", 100)
        prev_size = 100
        curr_section = main_section

        for page in doc:
            if page.number not in (doc[-1].number, doc[-2].number):
                rect = fitz.Rect(
                    page.rect.x0 + 20,
                    page.rect.y0 + 20,
                    page.rect.x1 - 20,
                    page.rect.y1 - 30,
                )

                blocks = page.get_text("dict", clip=rect)["blocks"]
                for block in blocks:
                    if "lines" in block.keys():
                        spans = block["lines"]
                        for span in spans:
                            data = span["spans"]
                            for lines in data:
                                cur_size = round(lines["size"], 2)

                                if lines["text"].strip() in (
                                    "Abstract",
                                    "Keywords",
                                    "LITERATURE CITED",
                                ):
                                    cur = Section(lines["text"], cur_size)
                                    curr_section = main_section.children[-1].children[
                                        -1
                                    ]
                                    curr_section.add_child(cur)
                                    cur.set_parent(curr_section)
                                    curr_section = cur

                                    prev_size = round(lines["size"], 2)

                                elif cur_size > prev_size:
                                    curr_section = curr_section.backtrack_add(
                                        lines["text"], cur_size
                                    )
                                    prev_size = curr_section.size

                                elif cur_size == prev_size:
                                    curr_section.extend(lines["text"])

                                else:
                                    cur = Section(lines["text"], cur_size)
                                    curr_section.add_child(cur)
                                    cur.set_parent(curr_section)
                                    curr_section = cur
                                    prev_size = round(lines["size"], 2)

        final_sections = main_section.children[-1].children

        if len(final_sections) > 1:
            return final_sections[-2].children + final_sections[-1].children
        else:
            return final_sections[-1].children
    except:
        logger.error(
            f"Error occurred in 'structure_doc_by_size_and_font': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'structure_doc_by_size_and_font': {traceback.format_exc()}"
        )


def preprocess_sections(sections):
    """
    Preprocess sections.

    Args:
        sections (list): List of sections to be preprocessed.

    Returns:
        list: Preprocessed sections.
    """
    try:
        # Preprocess sections
        first_section = Section("Keywords", 0)
        first_index = sections.index(first_section)
        sections = sections[first_index:]

        return sections
    except:
        logger.error(
            f"Error occurred in 'preprocess_sections': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'preprocess_sections': {traceback.format_exc()}"
        )


### SAME
def make_sections_dataframe(doc):
    """
    Generate a DataFrame containing the sections of a document.

    Args:
        doc (Document): The document to process.

    Returns:
        tuple: A tuple containing the sections list and the sections DataFrame.
    """

    try:
        # Get sections
        sections = get_sections(doc)
        sections = preprocess_sections(sections)

        content_nest = {}

        for section in sections:
            content_nest[section.content] = [section.print_contents()]

        sections_df = pd.DataFrame(content_nest, index=["text"]).T
        sections_df.name = doc.name
        return sections, sections_df

    except:
        logger.error(
            f"Error occurred in 'make_sections_dataframe': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'make_sections_dataframe': {traceback.format_exc()}"
        )


def make_references_dataframe(sections, sections_df):
    """
    Generate a dataframe of references from the given sections and sections_df.

    Args:
        sections (list): List of sections.
        sections_df (pd.DataFrame): DataFrame of sections.

    Returns:
        pd.DataFrame: DataFrame of references.
    """
    references_dictionary = {}
    references_text = sections[sections.index("LITERATURE CITED")].print_contents()
    references_clean = text_preprocess_for_reference_matching(references_text)

    try:
        for location, text in zip(sections_df.index[:-1], sections_df.values[:-1]):
            in_text_citations = get_in_text_citations(text.item())
            cleaned_in_text_citations = clean_in_text_citations(in_text_citations)
            author_year_pairs = list(
                filter(
                    lambda x: x != None,
                    map(process_citations, cleaned_in_text_citations),
                )
            )
            references_dictionary = find_citation_matches(
                author_year_pairs, references_clean, references_dictionary, location
            )

        references_df = pd.DataFrame(
            {k: [",".join(v)] for k, v in references_dictionary.items()},
            index=["section"],
        ).T.reset_index(names="reference")
        return references_df

    except:
        logger.error(
            f"Error occurred in 'make_references_dataframe': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'make_references_dataframe': {traceback.format_exc()}"
        )


def clean_in_text_citations(in_text_citations):
    """
    Cleans the in-text citations by removing unnecessary characters and splitting them into individual items.

    Parameters:
        in_text_citations (list): A list of in-text citations.

    Returns:
        list: A list of cleaned and split in-text citations.
    """
    try:
        return [
            item
            for group in [
                re.sub(r"\(|\)|see also|’s", "", item).split(",")
                for item in in_text_citations
            ]
            for item in group
        ]
    except:
        logger.error(
            f"Error occurred in 'clean_in_text_citations': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'clean_in_text_citations': {traceback.format_exc()}"
        )


def text_preprocess_for_reference_matching(references_text):
    """
    Preprocesses the given references text for reference matching.

    Args:
        references_text (str): The text containing the references.

    Returns:
        list: A list of cleaned references.
    """
    try:
        references_dirty = re.sub("\n", " ", references_text)
        references = " ".join(references_dirty.split())
        pattern = "[A-Z][A-Za-z, ]+[A-Z]{1,3}\. \d{4}\."
        references_clean = re.findall(pattern, references)

        for idx, ref in enumerate(references_clean):
            if idx == len(references_clean) - 1:
                # All the way to the end
                references_clean[idx] = references[references.find(ref) :]
            else:
                next_ref = references_clean[idx + 1]
                references_clean[idx] = references[
                    references.find(ref) : references.find(next_ref)
                ]

        return references_clean
    except:
        logger.error(
            f"Error occurred in 'text_preprocess_for_reference_matching': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'text_preprocess_for_reference_matching': {traceback.format_exc()}"
        )


### DIFF
def get_in_text_citations(text):
    """
    Extracts in-text citations from a given text.

    Args:
        text (str): The text from which to extract in-text citations.

    Returns:
        List[str]: A list of in-text citations found in the text.
    """
    IN_PARANTHESES_CITATION_REGEX = r"\([&\w\s., ]+\s\d{3,4}\)"
    AND_PATTERN = "\S+ & \S+ \(\d{3,4}\)"
    ONE_PATTERN = "[A-Z]\S+ \(\d{3,4}\)"
    ET_AL_PATTERN = "[A-Z][a-z] et al. \(\d{3,4}\)"
    IN_TEXT_CITATION_REGEX = (
        f"{IN_PARANTHESES_CITATION_REGEX}|{AND_PATTERN}|{ONE_PATTERN}|{ET_AL_PATTERN}"
    )
    return re.findall(IN_TEXT_CITATION_REGEX, text)


def process_citations(citation: str):
    """
    Process the given citation and extract the author(s) and year.

    Parameters:
        citation (str): The citation to process.

    Returns:
        tuple or list or None:
            - If the citation contains 2 authors, a tuple with the names of the authors and the year.
            - If the citation contains "et al.", a list with the name(s) and the year.
            - If the citation contains 1 author, a list with the name and the year.
            - If the citation is invalid or does not match any of the cases, None is returned.
    """
    try:
        # case 1: 2 authors
        if "&" in citation:
            tokens = citation.split()
            year = tokens[-1]
            names = " ".join(tokens[:-1])
            names_split = names.split("&")
            return ((names_split[0].strip(), names_split[1].strip()), year.strip())

        # case 2: et al
        if "et al." in citation:
            tokens = citation.split("et al.")
            return ([tokens[0].strip()], tokens[1].strip())

        # case 3: 1 author
        else:
            split = citation.split()
            if len(split) == 1:
                return None
            else:
                tokens = citation.split()
                year = tokens[-1]
                author = " ".join(tokens[:-1])
                return ([author.strip()], year.strip())
    except:
        logger.error(f"Error occurred in 'process_citations': {traceback.format_exc()}")
        raise Exception(
            f"Error occurred in 'process_citations': {traceback.format_exc()}"
        )


def find_citation_matches(author_year_pairs, full_references, data, location):
    """
    Find citation matches in the given list of author-year pairs and full references.

    Parameters:
    - author_year_pairs (list of tuples): A list of author-year pairs to search for.
    - full_references (list): A list of full references to search in.
    - data (dict): A dictionary to store the citation matches.
    - location (str): The location to associate with the citation matches.

    Returns:
    - data (dict): The updated dictionary with the citation matches.
    """
    try:
        for author_year_pair in author_year_pairs:
            authors, year = author_year_pair
            for reference in full_references:
                match = True
                if year in reference:
                    for author in authors:
                        if author not in reference:
                            match = False
                    if match:
                        dict_value = data.get(reference, [])
                        if dict_value == []:
                            data[reference] = []
                        if location not in dict_value:
                            data[reference] = data.get(reference, []) + [location]
                else:
                    continue
        return data
    except:
        logger.error(
            f"Error occurred in 'find_citation_matches': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'find_citation_matches': {traceback.format_exc()}"
        )


def convert_pdf_to_dataframes(doc):
    """
    Converts a PDF document into two separate dataframes.

    Args:
        doc (PDFDocument): The PDF document to be converted.

    Returns:
        tuple: A tuple containing two dataframes. The first dataframe contains
        the sections extracted from the document, while the second dataframe
        contains the references extracted from the document.
    """
    try:
        sections, sections_df = make_sections_dataframe(doc)
        references_df = make_references_dataframe(sections, sections_df)
        return sections_df, references_df
    except:
        logger.error(
            f"Error occurred in 'convert_pdf_to_dataframes': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'convert_pdf_to_dataframes': {traceback.format_exc()}"
        )


def sanitize_dataframe_for_download(df):
    """
    Sanitizes a pandas DataFrame for download by replacing newline characters and
    double quotes in string columns.

    Parameters:
        df (pandas.DataFrame): The DataFrame to be sanitized.

    Returns:
        pandas.DataFrame: The sanitized DataFrame.
    """
    try:
        for col in df.columns:
            if df[col].dtype == "object":
                try:
                    df[col] = df[col].str.replace("\n", " ").str.replace('"', "'")
                except AttributeError:
                    continue
        return df
    except:
        logger.error(
            f"Error occurred in 'sanitize_dataframe_for_download': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'sanitize_dataframe_for_download': {traceback.format_exc()}"
        )
