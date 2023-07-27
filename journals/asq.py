import itertools
import re
import traceback

import pandas as pd
from loguru import logger

ABSTRACT_KEY = ("AdvPSA35F", 10.0)
HEADERS_KEY = ("AdvP2A83", 10.0)


def make_sections_dataframe(doc):
    """
    Generate a dataframe with sections of text from a document.

    Parameters:
    - doc: The document from which to extract sections of text.

    Returns:
    - text_nest: A nested list of sections of text.
    - sections_df: A dataframe with the sections of text, indexed by "text" and with the document name as the column name.
    """
    try:
        text_nest = get_sections(doc)
        sections_df = pd.DataFrame(text_nest, index=["text"]).T
        sections_df.columns = [doc.name]
        return text_nest, sections_df
    except Exception as e:
        logger.error(
            f"Error occurred in 'make_sections_dataframe': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'make_sections_dataframe': {traceback.format_exc()}"
        )


def find_citation_matches(author_year_pairs, full_references, data, location):
    """
    Find citation matches based on author-year pairs, full references, data, and location.

    Parameters:
        - author_year_pairs (list): A list of tuples containing author names and publication years.
        - full_references (list): A list of full references.
        - data (dict): A dictionary containing reference data.
        - location (str): The location to match.

    Returns:
        - dict: The updated dictionary containing matched references and locations.
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

    except Exception as e:
        logger.error(
            f"Error occurred in 'find_citation_matches': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'find_citation_matches': {traceback.format_exc()}"
        )


def process_citations(citation_group: str):
    """
    Processes a citation group and returns a list of parsed citations.

    Args:
        citation_group (str): A string containing multiple citations separated by semicolons.

    Returns:
        list: A list of tuples representing the parsed citations. Each tuple contains two elements:
        - names (list): A list of author names.
        - year (str): The publication year of the citation.
    """
    citations = citation_group.split(";")
    results = []

    try:
        for citation in citations:
            try:
                # case 1: multiple authors
                if " and " in citation:
                    names, year = citation.split(",")[:-1], citation.split(",")[-1]
                    names = [
                        name.strip()
                        for name in names
                        if name.strip() not in ("", "e.g.")
                    ]
                    names = [name.replace(" and ", ",") for name in names]
                    results.append((names, year.strip()))

                # case 2: et al
                elif "et al." in citation:
                    citation = citation.replace("et al.", "")
                    names, year = citation.split(",")[:-1], citation.split(",")[-1]
                    names = [name.strip() for name in names if name.strip() != ""]
                    results.append((names, year.strip()))

                # case 3: 1 author
                else:
                    if "(" in citation:
                        author, year = citation.split()
                        results.append(([author], year[1:-1]))
                    else:
                        names, year = citation.split(",")[:-1], citation.split(",")[-1]
                        results.append(([names[-2].strip()], names[-1].strip()))

            except:
                results.append(([""], ""))

        return results

    except Exception as e:
        logger.error(
            f"Error occurred in 'find_citation_matches': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'find_citation_matches': {traceback.format_exc()}"
        )


def remove_prefix(citation):
    """
    Removes the prefix from a citation string.

    Parameters:
        citation (str): The citation string from which the prefix will be removed.

    Returns:
        str: The citation string without the prefix.
    """
    is_parantheses = False
    for idx, char in enumerate(citation):
        if char == "." and citation[idx - 1].islower() and not is_parantheses:
            return citation[idx + 2 :]
        if char == "(":
            is_parantheses = True
        if char == ")":
            is_parantheses = False

    return citation


def text_preprocess_for_reference_matching(references_text):
    """
    Preprocesses the given references text for reference matching.

    Args:
        references_text (str): The text containing the references.

    Returns:
        list: A list of cleaned references.

    """
    try:
        # START searching ONCE References tag found
        references_dirty = re.sub("\n", " ", references_text)
        references = " ".join(references_dirty.split())
        pattern = "[A-Z][A-Za-z,\-’.ˇ() ]+ \d{4} "
        references_clean = list(map(remove_prefix, re.findall(pattern, references)))

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
    except Exception as e:
        logger.error(
            f"Error occurred in 'text_preprocess_for_ref_matching': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'text_preprocess_for_ref_matching': {traceback.format_exc()}"
        )


def make_references_dataframe(text_nest, sections_df):
    """
    Generate a DataFrame containing references found in the given text nest and match them with the provided sections DataFrame.

    Parameters:
    - text_nest (dict): A dictionary containing the text nest.
    - sections_df (DataFrame): A pandas DataFrame containing the sections.

    Returns:
    - references_df (DataFrame): A pandas DataFrame containing the matched references.

    """
    try:
        references_dictionary = {}
        references_clean = text_preprocess_for_reference_matching(
            text_nest["REFERENCES"]
        )
        for location, text in zip(sections_df.index, sections_df.values):
            in_text_citations = get_in_text_citations(text.item())
            cleaned_in_text_citations = [
                citation if citation[0] != "(" else citation[1:-1]
                for citation in in_text_citations
            ]
            author_year_pairs_nested = [
                process_citations(citation)
                for citation in cleaned_in_text_citations
                if citation is not None
            ]
            author_year_pairs = list(
                itertools.chain.from_iterable(author_year_pairs_nested)
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


def get_in_text_citations(text):
    """
    Extracts in-text citations from a given text.

    Parameters:
        text (str): The text from which to extract in-text citations.

    Returns:
        List[str]: A list of in-text citations found in the text.

    Regex Patterns:
        - IN_PARANTHESES_CITATION_REGEX (str): Regular expression pattern for in-text citations enclosed in parentheses.
        - AND_PATTERN (str): Regular expression pattern for in-text citations with 'and' between two authors' names.
        - ONE_PATTERN (str): Regular expression pattern for in-text citations with a single author's name.
        - ET_AL_PATTERN (str): Regular expression pattern for in-text citations with 'et al.' after the first author's name.

    Returns:
        List[str]: A list of in-text citations found in the text.
    """
    IN_PARANTHESES_CITATION_REGEX = r"\([&\w\s.,\-; ]+\s\d{3,4}\)"
    AND_PATTERN = "\S+ and \S+ \(\d{3,4}\)"
    ONE_PATTERN = "[A-Z]\S+ \(\d{3,4}\)"
    ET_AL_PATTERN = "[A-Z][a-z] et al. \(\d{3,4}\)"
    IN_TEXT_CITATION_REGEX = (
        f"{IN_PARANTHESES_CITATION_REGEX}|{AND_PATTERN}|{ONE_PATTERN}|{ET_AL_PATTERN}"
    )
    return re.findall(IN_TEXT_CITATION_REGEX, text)


def convert_pdf_to_dataframes(doc):
    """
    Converts a PDF document to two dataframes: `sections_df` and `references_df`.

    Args:
        doc (PDF document): The PDF document to be converted.

    Returns:
        sections_df (DataFrame): A dataframe containing information about the sections in the document.
        references_df (DataFrame): A dataframe containing information about the references in the document.
    """
    sections, sections_df = make_sections_dataframe(doc)
    references_df = make_references_dataframe(sections, sections_df)
    return sections_df, references_df


def structure_doc_by_size_and_font(doc):
    """
    Generate a sequence of text from a document based on the size and font of each line.

    Args:
        doc (list): A list of pages in a document.

    Returns:
        tuple: A tuple containing two elements:
            - seqs (list): A list of sequences of text extracted from the document.
            - sorted_rest_fonts (list): A list of tuples containing font and size as keys and the corresponding
              extracted text as values. The list is sorted in descending order based on the size of the font.
    """
    try:
        fonts = {}
        seqs = []
        prev_size, prev_font = 0, 0
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    spans = block["lines"]
                    for span in spans:
                        data = span["spans"]
                        for lines in data:
                            cur_size = round(lines["size"], 2)
                            cur_font = lines["font"].split("+")[0]

                            key = (cur_font, cur_size)

                            if cur_size == prev_size and cur_font == prev_font:
                                latest_item = fonts[key][-1]
                                fonts[key][-1] = latest_item + " " + lines["text"]
                                seqs[-1] = seqs[-1] + " " + lines["text"]

                            else:
                                fonts[key] = fonts.get(key, []) + [lines["text"]]
                                seqs.append(lines["text"])

                            prev_size = cur_size
                            prev_font = cur_font

        sorted_fonts = sorted(fonts.items(), key=lambda x: x[0][1], reverse=True)
        return seqs, sorted_fonts
    except:
        logger.error(
            f"Error occurred in 'structure_doc_by_size_and_font': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'structure_doc_by_size_and_font': {traceback.format_exc()}"
        )


def get_headers(fonts):
    """
    Get the headers from a list of fonts.

    Parameters:
    - fonts (list): A list of fonts.

    Returns:
    - list: The headers extracted from the fonts.
    """
    try:
        first_part = []
        second_part = []
        for key, val in fonts:
            if key == ABSTRACT_KEY:
                first_part = val
            if key == HEADERS_KEY:
                second_part = val
        return first_part[:2] + second_part + first_part[2:]
    except:
        logger.error(f"Error occurred in 'get_headers': {traceback.format_exc()}")
        raise Exception(f"Error occurred in 'get_headers': {traceback.format_exc()}")


def find_earliest_uppercase_index(s):
    """
    Finds the index of the earliest uppercase character in a given string.

    Parameters:
    - s (str): The input string.

    Returns:
    - int: The index of the earliest uppercase character in the string, or the length of the string if no uppercase character is found.
    """
    for i, char in enumerate(s):
        if char.isalpha() and char.upper() == char:
            return i
    return len(s)


def get_text_nest(seqs, starting_text_nest, pdf_headers):
    """
    Generates a text nest based on a sequence of values.

    Args:
        seqs (list): A list of sequences to process.
        starting_text_nest (dict): The initial text nest.
        pdf_headers (list): A list of headers.

    Returns:
        dict: The updated text nest.
    """
    try:
        cur_header = "Other"
        for sequence in seqs[1:]:
            if sequence in pdf_headers:
                starting_text_nest[sequence] = ""
                cur_header = sequence
            else:
                if cur_header.startswith("Keyword"):
                    earliest_idx = find_earliest_uppercase_index(sequence)
                    keyword_part = sequence[:earliest_idx]
                    intro_part = sequence[earliest_idx:]
                    starting_text_nest[cur_header] = (
                        starting_text_nest.get(cur_header, "") + " " + keyword_part
                    )
                    cur_header = "Introduction"
                    starting_text_nest[cur_header] += " " + intro_part
                else:
                    starting_text_nest[cur_header] = (
                        starting_text_nest.get(cur_header, "") + " " + sequence
                    )

        return starting_text_nest
    except:
        logger.error(f"Error occurred in 'get_text_nest': {traceback.format_exc()}")
        raise Exception(f"Error occurred in 'get_text_nest': {traceback.format_exc()}")


def get_sections(doc):
    """
    Generates a nested structure of text sections from a given document.

    Parameters:
    - doc (Document): The document to be processed.

    Returns:
    - text_nest (NestedStructure): The nested structure of text sections.
    """
    try:
        seqs, fonts = structure_doc_by_size_and_font(doc)
        pdf_headers = get_headers(fonts)
        text_nest = get_text_nest(seqs, {}, pdf_headers)
        return text_nest
    except:
        logger.error(f"Error occurred in 'get_sections': {traceback.format_exc()}")
        raise Exception(f"Error occurred in 'get_sections': {traceback.format_exc()}")


def make_sections_dataframe(doc):
    """
    Generate a DataFrame containing sections of text from a given document.

    Parameters:
        doc (str): The document to extract sections from.

    Returns:
        tuple: A tuple containing two elements:
            - text_nest (list): A nested list containing the sections of text.
            - sections_df (DataFrame): A DataFrame containing the sections of text, with the "text" column as the index and the document name as the name of the DataFrame.
    """
    try:
        text_nest = get_sections(doc)
        sections_df = pd.DataFrame(text_nest, index=["text"]).T
        sections_df.name = doc.name
        return text_nest, sections_df
    except:
        logger.error(
            f"Error occurred in 'make_sections_dataframe': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'make_sections_dataframe': {traceback.format_exc()}"
        )
