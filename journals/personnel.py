import pandas as pd
import regex as re

from log import log_traceback
from section import Section


@log_traceback
def get_sections(doc):
    """
    Extracts sections from the given PDF document.

    Args:
        doc (fitz.Document): The PDF document object.

    Returns:
        list: A list of Section objects representing the extracted sections.
    """
    main_section = Section("", 100)
    prev_size = 100
    curr_section = main_section

    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block.keys():
                spans = block["lines"]
                for span in spans:
                    data = span["spans"]
                    for lines in data:
                        cur_size = round(lines["size"], 1)

                        if lines["text"].strip().lower() in (
                            "acknowledgements",
                            "references",
                            "appendix",
                            "endnotes",
                        ):
                            cur = Section(lines["text"], cur_size)
                            curr_section = main_section.children[-1].children[-1]
                            curr_section.add_child(cur)
                            cur.set_parent(curr_section)
                            curr_section = cur

                        elif cur_size > prev_size:
                            curr_section = curr_section.backtrack_add(
                                lines["text"], cur_size
                            )

                        elif cur_size == prev_size:
                            curr_section.extend(lines["text"])

                        else:
                            cur = Section(lines["text"], cur_size)
                            curr_section.add_child(cur)
                            cur.set_parent(curr_section)
                            curr_section = cur

                        prev_size = round(lines["size"], 1)

    return main_section.children[-1].children[-1].children


@log_traceback
def make_sections_dataframe(doc):
    """
    Generate a pandas DataFrame containing the sections and their corresponding content from a PDF document.

    Parameters:
    path (str): The path to the PDF document.

    Returns:
    Tuple[Dict[str, List[str]], pd.DataFrame]: A tuple containing two elements:
        - content_nest (Dict[str, List[str]]): A dictionary where the keys are the section content and the values are lists of section contents.
        - sections_df (pd.DataFrame): A pandas DataFrame containing the section content as rows and a single column named "text".
          The index of the DataFrame is the section content and the name of the DataFrame is the name of the PDF document.
    """
    sections = get_sections(doc)
    sections = preprocess_sections(sections)

    content_nest = {}

    for section in sections:
        content_nest[section.content] = [section.print_contents()]

    sections_df = pd.DataFrame(content_nest, index=["text"]).T
    sections_df.name = doc.name
    return content_nest, sections_df


@log_traceback
def text_preprocess_for_reference_matching(references_text):
    references_dirty = re.sub("\n", " ", references_text)
    references = " ".join(references_dirty.split())
    pattern = r"(?:[\p{L}][\p{L}\s]+,(?:(?:\s|\-)[A-Z]\.){1,3}(?:,(?: . . .)?\s(?:&\s?)?)?)+ \(\d{4}\)"
    """
    Preprocesses the given references text for reference matching.

    Args:
        references_text (str): The text containing the references.

    Returns:
        list: A list of cleaned references.
    """
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


@log_traceback
def find_citation_matches(author_year_pairs, full_references, data, location):
    """
    Find citation matches in a list of author-year pairs and full references.

    Args:
        author_year_pairs (List[Tuple[List[str], int]]): A list of tuples, where each tuple contains a list of authors and a year.
        full_references (List[str]): A list of full references.
        data (Dict[str, List[str]]): A dictionary where the keys are full references and the values are lists of locations.
        location (str): The location to be added to the list of locations for each matching reference.

    Returns:
        Dict[str, List[str]]: The updated data dictionary with the locations added to the matching references.
    """
    for author_year_pair in author_year_pairs:
        authors, year = author_year_pair
        for reference in full_references:
            match = True
            if f"({year})" in reference:
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


@log_traceback
def preprocess_sections(sections):
    """
    Preprocesses the sections list by removing all elements after the "REFERENCES" section.

    Args:
        sections (list): A list of sections.

    Returns:
        list: The preprocessed sections list with all elements after the "REFERENCES" section removed.
    """
    references_section_index = sections.index("REFERENCES")
    sections = sections[1 : references_section_index + 1]
    return sections


@log_traceback
def find_citation_matches(author_year_pairs, full_references, data, location):
    """
    This function finds citation matches based on the given author-year pairs, full references, data, and location.

    Parameters:
        - author_year_pairs (list): A list of tuples containing author names and publication years.
        - full_references (list): A list of full references.
        - data (dict): A dictionary containing data.
        - location (str): The location to match.

    Returns:
        - data (dict): A dictionary containing the updated data with citation matches.
    """
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
        if not has_matched:
            print(author_year_pair)
            # print(full_references)

    return data


@log_traceback
def process_citations(citation_group: str):
    """
    Processes a group of citations and extracts relevant information.

    Parameters:
    - citation_group (str): A string representing a group of citations separated by ';'

    Returns:
    - results (list): A list of tuples containing extracted information from each citation. Each tuple contains:
        - names (list): A list of last names of authors in the citation.
        - year (str): The year associated with the citation.

    Example:
    >>> process_citations("Smith, John; Johnson, Jane, 2020; Brown et al., 2019")
    [('John', '2020'), (['Jane'], '2020'), (['Brown'], '2019')]
    """
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
                        [token.strip() for token in tokens[:-1] if token.strip() != ""],
                        tokens[-1].strip(),
                    )
                )

            # case 3: 1 author
            else:
                if "(" in citation:
                    author, year = citation.split()
                    results.append(([author.split()[-1].strip()], year[1:-1].strip()))
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


@log_traceback
def remove_prefix(citation):
    """
    Generate a function comment for the given function body in a markdown code block with the correct language syntax.

    Args:
        citation (str): The citation from which to remove the prefix.

    Returns:
        str: The citation with the prefix removed.
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


@log_traceback
def text_preprocess_for_reference_matching(references_text):
    """
    Preprocesses the given references text for reference matching.

    Args:
        references_text (str): The text containing the references.

    Returns:
        list: A list of cleaned references.

    Raises:
        None.
    """
    references_dirty = re.sub("\n", " ", references_text)
    references = " ".join(references_dirty.split())
    pattern = r"(?:[\p{L}][\p{L}\s]+,(?:(?:\s|\-)[A-Z]\.){1,3}(?:,(?: . . .)?\s(?:&\s?)?)?)+ \(\d{4}\)"
    references_clean = re.findall(pattern, references)
    for idx, ref in enumerate(references_clean):
        if idx == len(references_clean) - 1:
            references_clean[idx] = references[references.find(ref) :]
        else:
            next_ref = references_clean[idx + 1]
            references_clean[idx] = references[
                references.find(ref) : references.find(next_ref)
            ]

    return references_clean


@log_traceback
def make_references_dataframe(sections, sections_df):
    """
    Generate a dataframe of references from given sections and sections dataframe.

    Args:
        sections (dict): A dictionary containing different sections of text.
        sections_df (pd.DataFrame): A pandas dataframe containing the sections as rows.

    Returns:
        pd.DataFrame: A dataframe with the references extracted from the sections.

    """
    references_dictionary = {}

    references_text = sections["REFERENCES"][0]
    references_clean = text_preprocess_for_reference_matching(references_text)
    for location, text in zip(sections_df.index, sections_df.values):
        in_text_citations = get_in_text_citations(text.item())
        # clean
        cleaned_in_text_citations = clean_in_text_citations(in_text_citations)
        processed_citations = [
            process_citations(citation) for citation in cleaned_in_text_citations
        ]
        # format
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
        {k: [",".join(v)] for k, v in references_dictionary.items()}, index=["section"]
    ).T.reset_index(names="reference")
    return references_df


@log_traceback
def get_in_text_citations(text):
    """
    Extracts in-text citations from a given text.

    Args:
        text (str): The input text from which to extract the in-text citations.

    Returns:
        List[str]: A list of in-text citations found in the input text.

    """
    IN_PARANTHESES_CITATION_REGEX = "\([&\w\\.\s,\-; ]+\s\d{3,4}(?::\s\d{1,4})?\s\)"
    AND_PATTERN = "\S+ and \S+ \(\d{3,4}\)"
    ONE_PATTERN = "[A-Z]\S+ \(\d{3,4}\)"
    ET_AL_PATTERN = "[A-Z][a-z] et al. \(\d{3,4}\)"
    IN_TEXT_CITATION_REGEX = (
        f"{IN_PARANTHESES_CITATION_REGEX}|{AND_PATTERN}|{ONE_PATTERN}|{ET_AL_PATTERN}"
    )
    return re.findall(IN_TEXT_CITATION_REGEX, text)


@log_traceback
def clean_in_text_citations(in_text_citations):
    """
    Cleans the in-text citations in a list of citations.

    Parameters:
    - in_text_citations (list): A list of strings representing the in-text citations.

    Returns:
    - cleaned_citations (list): A list of strings representing the cleaned in-text citations.
    """
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

        if citation.startswith("(see "):
            citation = citation[5:]
        elif "e.g." in citation or "i.e." in citation:
            citation = citation[7:]
        elif citation.startswith("("):
            citation = citation[1:]
        else:
            citation = citation
        cleaned_citations.append(citation)
    return cleaned_citations


@log_traceback
def convert_pdf_to_dataframes(doc):
    """
    Converts a PDF document into pandas DataFrames.

    Parameters:
        doc (PDF document): The PDF document to be converted.

    Returns:
        sections_df (pandas DataFrame): The DataFrame containing the sections of the document.
        references_df (pandas DataFrame): The DataFrame containing the references of the document.
    """
    sections, sections_df = make_sections_dataframe(doc)
    references_df = make_references_dataframe(sections, sections_df)
    return sections_df, references_df
