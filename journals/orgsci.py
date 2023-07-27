import fitz
import re
from loguru import logger
import pandas as pd
from section import Section
import traceback
from typing import List, Any, Tuple, Dict, Union


def get_sections(doc: fitz.Document) -> List:
    """
    Extracts sections from the given PDF document.

    Args:
        doc (fitz.Document): The PDF document object.

    Returns:
        list: A list of Section objects representing the extracted sections.
    """
    try:
        main_section = Section("", 100)

        prev_size = 100
        curr_section = main_section

        for page in doc:
            rect = fitz.Rect(
                page.rect.x0 + 40,
                page.rect.y0 + 60,
                page.rect.x1 - 40,
                page.rect.y1 - 40,
            )

            dict = page.get_text("dict", clip=rect)

            blocks = dict["blocks"]
            for block in blocks:
                if "lines" in block.keys():
                    spans = block["lines"]
                    for span in spans:
                        data = span["spans"]
                        for lines in data:
                            cur_size = round(lines["size"], 1)

                            # Manual Override for References
                            if lines["text"].strip() in (
                                "Acknowledgements",
                                "References",
                                "Appendix",
                                "Endnotes",
                            ):
                                cur = Section(lines["text"], cur_size)
                                curr_section = main_section.children[-1].children[-1]
                                curr_section.add_child(cur)
                                cur.set_parent(curr_section)
                                curr_section = cur

                                prev_size = round(lines["size"], 1)

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
                                prev_size = round(lines["size"], 1)

        # orgsci
        return main_section.children[-1].children[-1].children

    except Exception as e:
        logger.exception(
            f"Error occurred while extracting sections from the PDF document: {traceback.format_exc()}",
        )
        raise Exception(
            f"Error occurred while extracting sections from the PDF document: {traceback.format_exc()}",
        )


def preprocess_sections(sections: List) -> List:
    """
    Preprocesses the extracted sections.

    Args:
        sections (List): List of Section objects representing the extracted sections.

    Returns:
        List: Preprocessed list of Section objects.
    """
    try:
        add_new_section = False

        # Preprocess sections
        abstract_section = Section("Abstract. ", 0)
        abstract_index = sections.index(abstract_section)
        abstract_text = sections.pop(abstract_index + 1)
        sections[abstract_index].add_child(abstract_text)

        sections_tmp = sections.copy()
        earliest_index = 1000
        txt = ""

        # Fit all text that belongs in paragraph into one "Introduction" paragraph
        for idx, section in enumerate(sections_tmp):
            if len(section.content) > 225:
                add_new_section = True
                if min(earliest_index, idx) != earliest_index:
                    earliest_index = idx
                sections.remove(section)
                txt += section.content

        if add_new_section:
            new_section = Section("Introduction", 20)
            new_section.add_child(Section(txt, 15))
            sections[earliest_index] = new_section

        sections = sections[abstract_index:]

        return sections

    except Exception as e:
        logger.error(
            "Error occurred while preprocessing the sections: {}",
            traceback.format_exc(),
        )
        raise Exception(
            "Error occurred while preprocessing the sections: {}",
            traceback.format_exc(),
        )


def make_sections_dataframe(doc: Any) -> Tuple:
    """
    Creates a DataFrame with sections and their contents from the PDF document.

    Args:
        doc (Any): The PDF document.

    Returns:
        Tuple: A tuple containing the list of Section objects and the DataFrame.
    """
    try:
        # Get sections
        sections = get_sections(doc)
        sections = preprocess_sections(sections)

        content_nest = {}

        for section in sections:
            content_nest[section.content] = [section.print_contents()]

        sections_df = pd.DataFrame(content_nest, index=["text"]).T

        # Add keywords to sections
        abstract_text = sections_df.iloc[0].item()
        abstract, keywords = abstract_text.split("Keywords")
        cleaned_keywords = [keyword.strip() for keyword in keywords.split("•")]
        new_row = pd.DataFrame({"text": str(cleaned_keywords)}, index=["Keywords"])
        sections_df = pd.concat([new_row, sections_df])

        sections_df.name = doc.name
        return sections, sections_df

    except Exception as e:
        logger.error(
            "Error occurred while creating the DataFrame with sections: {}",
            traceback.format_exc(),
        )

        raise Exception(
            "Error occurred while creating the DataFrame with sections: {}",
            traceback.format_exc(),
        )


def make_sections_dataframe(doc: Any) -> Tuple:
    """
    Creates a DataFrame with sections and their contents from the PDF document.

    Args:
        doc (Any): The PDF document.

    Returns:
        Tuple: A tuple containing the list of Section objects and the DataFrame.
    """
    try:
        # Get sections
        sections = get_sections(doc)
        sections = preprocess_sections(sections)

        content_nest = {}

        for section in sections:
            content_nest[section.content] = [section.print_contents()]

        sections_df = pd.DataFrame(content_nest, index=["text"]).T

        # Add keywords to sections
        abstract_text = sections_df.iloc[0].item()
        abstract, keywords = abstract_text.split("Keywords")
        cleaned_keywords = [keyword.strip() for keyword in keywords.split("•")]
        new_row = pd.DataFrame({"text": str(cleaned_keywords)}, index=["Keywords"])
        sections_df = pd.concat([new_row, sections_df])

        sections_df.name = doc.name
        return sections, sections_df

    except Exception as e:
        logger.error(
            "Error occurred while creating the DataFrame with sections: {}",
            traceback.format_exc(),
        )
        raise Exception(
            "Error occurred while creating the DataFrame with sections: {}",
            traceback.format_exc(),
        )


def clean_in_text_citations(in_text_citations: List[str]) -> List[str]:
    """
    Cleans in-text citations by removing unnecessary characters.

    Args:
        in_text_citations (List[str]): List of in-text citations.

    Returns:
        List[str]: Cleaned list of in-text citations.
    """
    try:
        return [
            item
            for group in [
                [
                    c.strip()  # Remove whitespace
                    for c in citation[1:-1].split(",")  # Remove '(' and ')'
                    if any(char.isdigit() for char in c)
                ]  # Remove any that doesn't have digits (year)
                for citation in in_text_citations
            ]
            for item in group
        ]

    except Exception as e:
        logger.error(
            "Error occurred while cleaning in-text citations: {}",
            traceback.format_exc(),
        )
        raise Exception(
            "Error occurred while cleaning in-text citations: {}",
            traceback.format_exc(),
        )


def make_references_dataframe(sections: List, sections_df: Any) -> pd.DataFrame:
    """
    Creates a DataFrame with references and their corresponding sections.

    Args:
        sections (List): List of Section objects representing the extracted sections.
        sections_df (Any): The DataFrame containing sections and their contents.

    Returns:
        pd.DataFrame: DataFrame with references and their corresponding sections.
    """
    try:
        references_dictionary = {}
        references_text = sections[-1].print_contents()
        references_clean = text_preprocess_for_reference_matching(references_text)

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

    except Exception as e:
        logger.error(
            "Error occurred while creating the DataFrame with references: {}",
            traceback.format_exc(),
        )
        raise Exception(
            "Error occurred while creating the DataFrame with references: {}",
            traceback.format_exc(),
        )


def text_preprocess_for_reference_matching(references_text: str) -> List[str]:
    """
    Preprocesses the references text for matching.

    Args:
        references_text (str): The references text.

    Returns:
        List[str]: List of preprocessed references.
    """
    try:
        # START searching ONCE References tag found
        references_dirty = re.sub("\n", " ", references_text)
        references_dirty = " ".join(references_dirty.split())
        references = re.sub("([0-9]|html|\))\s?\.", r"\g<0>\n", references_dirty)

        # Make list of references
        pattern = (
            r"[A-ZÆØÅæøå][ÆØÅæøåA-Za-z]+.*[A-Z]{1,3},? .*\(\d{4}\).*[html|\d|\)]\."
        )
        references_clean = re.findall(pattern, references)
        return references_clean

    except Exception as e:
        logger.error(
            "Error occurred while preprocessing references for matching: {}",
            traceback.format_exc(),
        )
        raise Exception(
            "Error occurred while preprocessing references for matching: {}",
            traceback.format_exc(),
        )


def get_in_text_citations(text: str) -> List[str]:
    """
    Extracts in-text citations from the given text.

    Args:
        text (str): The text to extract in-text citations from.

    Returns:
        List[str]: List of in-text citations.
    """
    try:
        IN_TEXT_CITATION_REGEX = r"\([\w\s.,]+\s\d{3,4}\s?\)"
        return re.findall(IN_TEXT_CITATION_REGEX, text)

    except Exception as e:
        logger.error(
            "Error occurred while extracting in-text citations: {}",
            traceback.format_exc(),
        )
        raise Exception(
            "Error occurred while extracting in-text citations: {}",
            traceback.format_exc(),
        )


def process_citations(
    citation: str,
) -> Union[None, Tuple[Tuple[str, str], str], Tuple[List[str], str]]:
    """
    Processes the citation text and returns author-year pairs.

    Args:
        citation (str): The citation text.

    Returns:
        Union[None, Tuple[Tuple[str, str], str], Tuple[List[str], str]]:
            - None if the citation format is not recognized.
            - Tuple[Tuple[str, str], str] for cases with two authors.
            - Tuple[List[str], str] for cases with 'et al.' format or one author.
    """
    try:
        # case 1: 2 authors
        if " and " in citation:
            tokens = citation.split()
            year = tokens[-1]
            names = " ".join(tokens[:-1])
            names_split = names.split(" and ")
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
    except Exception:
        logger.error(
            "Error occurred while processing citations: {}", traceback.format_exc()
        )
        raise Exception(
            "Error occurred while processing citations: {}", traceback.format_exc()
        )


def find_citation_matches(
    author_year_pairs: List[Tuple[str, str]],
    full_references: List[str],
    data: Dict[str, List],
    location: Any,
) -> Dict[str, List]:
    """
    Finds citation matches in the full references.

    Args:
        author_year_pairs (List[Tuple[str, str]]): List of author-year pairs.
        full_references (List[str]): List of full references.
        data (Dict[str, List]): Dictionary to store citation matches.
        location (Any): The location of the citation.

    Returns:
        Dict[str, List]: Dictionary containing citation matches.
    """
    try:
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
    except Exception:
        logger.error(
            "Error occurred while finding citation matches: {}", traceback.format_exc()
        )
        raise Exception(
            "Error occurred while finding citation matches: {}", traceback.format_exc()
        )


def convert_pdf_to_dataframes(path: Any) -> Tuple[Any, Any]:
    """
    Converts a PDF document to DataFrames containing sections and references.

    Args:
        path (Any): The path to the PDF document.

    Returns:
        Tuple[Any, Any]: A tuple containing the sections DataFrame and the references DataFrame.
    """
    try:
        sections, sections_df = make_sections_dataframe(path)
        references_df = make_references_dataframe(sections, sections_df)
        return sections_df, references_df

    except Exception as e:
        logger.error(
            "Error occurred while converting PDF to DataFrames: {}",
            traceback.format_exc(),
        )

        raise Exception(
            "Error occurred while converting PDF to DataFrames: {}",
            traceback.format_exc(),
        )


def sanitize_dataframe_for_download(df: Any) -> Any:
    """
    Sanitizes a DataFrame for download by replacing characters.

    Args:
        df (Any): The DataFrame to be sanitized.

    Returns:
        Any: The sanitized DataFrame.
    """
    try:
        for col in df.columns:
            if df[col].dtype == "object":
                try:
                    df[col] = df[col].str.replace("\n", " ").str.replace('"', "'")
                except AttributeError:
                    continue
        return df

    except Exception as e:
        logger.error(
            "Error occurred while sanitizing the DataFrame: {}", traceback.format_exc()
        )

        raise Exception(
            "Error occurred while sanitizing the DataFrame: {}", traceback.format_exc()
        )
