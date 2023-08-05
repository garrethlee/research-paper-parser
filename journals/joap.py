import regex as re
import traceback

import pandas as pd
from loguru import logger


def structure_doc_by_size_and_font(doc):
    """
    Generates a dictionary that structures a document by font size and font type.

    Parameters:
        doc (object): The document to structure.

    Returns:
        tuple: A tuple containing two elements:
            - A list of sequences of text lines.
            - A dictionary that maps font size and font type to a list of text lines.

    Raises:
        Exception: If an error occurs while structuring the document.
    """
    rest_fonts = {}
    seqs = []
    prev_size, prev_font = 0, 0
    try:
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block.keys():
                    spans = block["lines"]
                    for span in spans:
                        data = span["spans"]
                        for lines in data:
                            cur_size = round(lines["size"], 2)
                            cur_font = lines["font"].split("+")[0]

                            key = (cur_font, cur_size)

                            if cur_size == prev_size and cur_font == prev_font:
                                latest_item = rest_fonts[key][-1]

                                rest_fonts[key][-1] = latest_item + " " + lines["text"]
                                seqs[-1] = seqs[-1] + " " + lines["text"]

                            else:
                                rest_fonts[key] = rest_fonts.get(key, []) + [
                                    lines["text"]
                                ]
                                seqs.append(lines["text"])

                            prev_size = cur_size
                            prev_font = cur_font

        sorted_fonts = dict(
            sorted(rest_fonts.items(), key=lambda x: x[0][1], reverse=True)
        )
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
    Retrieves the headers from the given `fonts` dictionary.

    Parameters:
        fonts (dict): A dictionary containing font information.

    Returns:
        Any: The headers stored in the `fonts` dictionary.

    Raises:
        Exception: If an error occurs while retrieving the headers.
    """
    HEADER_KEY = ("Times-Bold", 10.0)
    try:
        return fonts[HEADER_KEY]
    except KeyError as e:
        logger.error(f"Error occurred in 'get_headers': {traceback.format_exc()}")
        raise Exception(f"Error occurred in 'get_headers': {traceback.format_exc()}")


def get_text_nest(seqs, starting_text_nest, pdf_headers):
    """
    Get the nested text from a list of sequences.

    Args:
        seqs (List[str]): The list of sequences to process.
        starting_text_nest (Dict[str, str]): The starting text nest.
        pdf_headers (List[str]): The list of PDF headers.

    Returns:
        Dict[str, str]: The updated starting text nest.

    Raises:
        Exception: If an error occurs during the execution of the function.
    """
    try:
        cur_header = "Other"
        prev_sequence = ""
        for sequence in seqs:
            if sequence in pdf_headers:
                starting_text_nest[sequence] = ""
                cur_header = sequence
            else:
                if prev_sequence.startswith("Keywords"):
                    cur_header = "Keywords"
                    starting_text_nest[cur_header] = (
                        starting_text_nest.get(cur_header, "") + " " + sequence
                    )
                    cur_header = "Abstract"
                else:
                    starting_text_nest[cur_header] = (
                        starting_text_nest.get(cur_header, "") + " " + sequence
                    )

            prev_sequence = sequence

        return starting_text_nest
    except:
        logger.error(f"Error occurred in 'get_text_nest': {traceback.format_exc()}")
        raise Exception(f"Error occurred in 'get_text_nest': {traceback.format_exc()}")


def find_earliest_uppercase_index(s):
    """
    Finds the index of the earliest uppercase character in a given string.

    Args:
        s (str): The input string to search for an uppercase character.

    Returns:
        int: The index of the earliest uppercase character in the string. If no uppercase character is found, returns the length of the string.

    Raises:
        Exception: If an error occurs during the execution of the function.

    """
    try:
        for i, char in enumerate(s):
            if char.isalpha() and char.upper() == char:
                return i
        return len(s)
    except:
        logger.error(
            f"Error occurred in 'find_earliest_uppercase_index': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'find_earliest_uppercase_index': {traceback.format_exc()}"
        )


def get_sections(doc):
    """
    Retrieves the sections from a given document.

    Parameters:
    - doc: A document object representing the document to retrieve sections from.

    Returns:
    - text_nest: A nested data structure containing the retrieved sections.

    Raises:
    - Exception: If an error occurs during the retrieval of sections.
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
    Generate a DataFrame of sections from the given document.

    Parameters:
        doc (str): The document from which to extract sections.

    Returns:
        tuple: A tuple containing two elements:
            - text_nest (list): A nested list of the extracted sections.
            - sections_df (pandas.DataFrame): A DataFrame containing the sections with the 'text' column.

    Raises:
        Exception: If an error occurs during the process, an exception is raised with the error message.
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


def find_citation_matches(author_year_pairs, full_references, data, location):
    """
    Finds citation matches based on author-year pairs, full references, data, and location.

    Args:
        author_year_pairs (list): A list of tuples containing author names and years.
        full_references (list): A list of full reference strings.
        data (dict): A dictionary containing citation matches.
        location (str): A string representing the location of the citation match.

    Returns:
        dict: A dictionary containing the updated citation matches.
    """
    try:
        for author_year_pair in author_year_pairs:
            authors, year = author_year_pair
            has_matched = False
            for reference in full_references:
                match = True
                if year in reference:
                    for author in authors:
                        if author not in reference:
                            match = False
                    if match:
                        has_matched = True
                        dict_value = data.get(reference, [])
                        if dict_value == []:
                            data[reference] = []
                        if location not in dict_value:
                            data[reference] = data.get(reference, []) + [location]

        return data
    except:
        logger.error(
            f"Error occurred in 'find_citation_matches': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'find_citation_matches': {traceback.format_exc()}"
        )


def process_citations(citation_group: str):
    """
    Process a group of citations and extract relevant information.

    Args:
        citation_group (str): A string containing multiple citations separated by ';'.

    Returns:
        list: A list of tuples containing the extracted information from each citation.
            Each tuple consists of:
                - A list of authors' last names.
                - The publication year.

    Raises:
        Exception: If an error occurs during the processing of citations.
    """
    try:
        citations = citation_group.split(";")
        results = []
        for citation in citations:
            try:
                # case 1: &
                if " & " in citation:
                    tokens = citation.split(",")
                    year = tokens[-1]
                    names = ",".join(tokens[:-1])
                    names = names.replace(" & ", ",")
                    names_split = names.split(",")
                    results.append(
                        (
                            [
                                name.split()[-1].strip()
                                for name in names_split
                                if name.strip()
                                not in ("e.g.,", "", "e.g.,", "quoted", "in")
                            ],
                            year.strip(),
                        )
                    )

                # case 2: et al
                elif "et al." in citation:
                    citation = citation.replace("et al.", "")
                    tokens = citation.split(",")
                    results.append(
                        (
                            [
                                token.strip()
                                for token in tokens[:-1]
                                if token.strip() != ""
                            ],
                            tokens[-1].strip(),
                        )
                    )

                # case 3: 1 author
                else:
                    if "(" in citation:
                        author, year = citation.split()
                        results.append(
                            ([author.split()[-1].strip()], year[1:-1].strip())
                        )
                    else:
                        citation_split = citation.split(",")
                        results.append(
                            (
                                [citation_split[-2].split()[-1].strip()],
                                citation_split[-1].split(":")[0].strip(),
                            )
                        )
            except:
                results.append(None)

        return results
    except:
        logger.error(f"Error occurred in 'process_citations': {traceback.format_exc()}")
        raise Exception(
            f"Error occurred in 'process_citations': {traceback.format_exc()}"
        )


def remove_prefix(citation):
    """
    Remove the prefix from a citation string.

    Parameters:
        citation (str): The citation string.

    Returns:
        str: The citation string without the prefix.

    Raises:
        Exception: If an error occurs in the function.
    """
    try:
        is_parantheses = False
        for idx, char in enumerate(citation):
            if char == "." and citation[idx - 1].islower() and not is_parantheses:
                return citation[idx + 2 :]
            if char == "(":
                is_parantheses = True
            if char == ")":
                is_parantheses = False
        return citation
    except:
        logger.error(f"Error occurred in 'remove_prefix': {traceback.format_exc()}")
        raise Exception(f"Error occurred in 'remove_prefix': {traceback.format_exc()}")


def text_preprocess_for_reference_matching(references_text):
    """
    Preprocesses the given references text for reference matching.

    Args:
        references_text (str): The text containing the references.

    Returns:
        list: A list of cleaned references.

    Raises:
        Exception: If an error occurs during preprocessing.
    """
    try:
        references_dirty = re.sub("\n", " ", references_text)
        references = " ".join(references_dirty.split())
        pattern = r"(?:[\p{L}][\p{L}\s]+,(?:(?:\s|\-)[A-Z]\.){1,3}(?:,(?: . . .)?\s(?:&\s?)?)?)+ \(\d{4}\)"
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


def make_references_dataframe(text_nest, sections_df):
    """
    Generate a dataframe of references based on a nested text and a dataframe of sections.

    Args:
        text_nest (dict): A nested text object containing the references.
        sections_df (pd.DataFrame): A dataframe of sections.

    Returns:
        pd.DataFrame: A dataframe of references.

    Raises:
        Exception: If an error occurs during the execution of the function.
    """
    try:
        references_dictionary = {}
        references_clean = text_preprocess_for_reference_matching(
            text_nest["References"]
        )
        for location, text in zip(sections_df.index, sections_df.values):
            in_text_citations = get_in_text_citations(text.item())
            cleaned_in_text_citations = clean_in_text_citations(in_text_citations)
            processed_citations = [
                process_citations(citation) for citation in cleaned_in_text_citations
            ]
            author_year_pairs = list(
                filter(
                    lambda x: x is not None,
                    (item for group in processed_citations for item in group),
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


def get_in_text_citations(text):
    """
    Return a list of in-text citations found in the given text.

    Parameters:
        text (str): The text to search for in-text citations.

    Returns:
        list: A list of strings representing the in-text citations found in the text.
    """
    try:
        IN_PARANTHESES_CITATION_REGEX = "\([&\w\\.\s,\-; ]+\s\d{3,4}(?::\s\d{1,4})?\s\)"
        AND_PATTERN = "\S+ and \S+ \(\d{3,4}\)"
        ONE_PATTERN = "[A-Z]\S+ \(\d{3,4}\)"
        ET_AL_PATTERN = "[A-Z][a-z] et al. \(\d{3,4}\)"
        IN_TEXT_CITATION_REGEX = f"{IN_PARANTHESES_CITATION_REGEX}|{AND_PATTERN}|{ONE_PATTERN}|{ET_AL_PATTERN}"
        return re.findall(IN_TEXT_CITATION_REGEX, text)
    except:
        logger.error(
            f"Error occurred in 'get_in_text_citations': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'get_in_text_citations': {traceback.format_exc()}"
        )


def clean_in_text_citations(in_text_citations):
    """
    Cleans the in-text citations by applying a series of transformations to each citation.

    Parameters:
    - in_text_citations (list): A list of in-text citations to be cleaned.

    Returns:
    - cleaned_citations (list): A list of cleaned in-text citations.

    Raises:
    - Exception: If an error occurs during the cleaning process.
    """
    try:
        cleaned_citations = []
        for citation in in_text_citations:
            citation = re.sub(" \((\d{4})\)", r", \1", citation)
            if " and " in citation:
                citation = citation.replace(" and ", " & ")
            if "- " in citation:
                citation = citation.replace("- ", "")
            if "’s" in citation:
                citation = citation.replace("’s", "")
            if citation.endswith(" )"):
                citation = citation[:-2]
            if citation.startswith("( "):
                citation = citation[2:]
            elif citation.startswith("(for an exception see"):
                citation = citation[22:]
            elif "e.g." in citation or "i.e." in citation:
                citation = citation[8:]
            else:
                citation = citation
            cleaned_citations.append(citation)
        return cleaned_citations
    except:
        logger.error(
            f"Error occurred in 'clean_in_text_citations': {traceback.format_exc()}"
        )
        raise Exception(
            f"Error occurred in 'clean_in_text_citations': {traceback.format_exc()}"
        )


def convert_pdf_to_dataframes(doc):
    """
    Converts a PDF document to Pandas DataFrames.

    Parameters:
        doc (PDF document): The PDF document to convert.

    Returns:
        sections_df (DataFrame): The DataFrame containing the sections of the document.
        references_df (DataFrame): The DataFrame containing the references of the document.

    Raises:
        Exception: If an error occurs during the conversion process.
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
