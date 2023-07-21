import fitz
import re
import pandas as pd
from section import *


def get_sections(doc):
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

            dict = page.get_text("dict", clip=rect)
            blocks = dict["blocks"]
            for block in blocks:
                if "lines" in block.keys():
                    spans = block["lines"]
                    for span in spans:
                        data = span["spans"]
                        for lines in data:
                            cur_size = round(lines["size"], 2)

                            # Manual Override for References
                            if lines["text"].strip() in (
                                "Abstract",
                                "Keywords",
                                "LITERATURE CITED",
                            ):
                                cur = Section(lines["text"], cur_size)
                                curr_section = main_section.children[-1].children[-1]
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


### DIFF
def preprocess_sections(sections):
    # Preprocess sections
    first_section = Section("Keywords", 0)
    first_index = sections.index(first_section)
    sections = sections[first_index:]

    return sections


### SAME
def make_sections_dataframe(doc):
    # Get sections
    sections = get_sections(doc)
    sections = preprocess_sections(sections)

    content_nest = {}

    for section in sections:
        content_nest[section.content] = [section.print_contents()]

    sections_df = pd.DataFrame(content_nest, index=["text"]).T
    sections_df.name = doc.name
    return sections, sections_df


### DIFF
def make_references_dataframe(sections, sections_df):
    references_dictionary = {}
    references_text = sections[sections.index("LITERATURE CITED")].print_contents()
    references_clean = text_preprocess_for_reference_matching(references_text)

    for location, text in zip(sections_df.index[:-1], sections_df.values[:-1]):
        in_text_citations = get_in_text_citations(text.item())
        cleaned_in_text_citations = clean_in_text_citations(in_text_citations)
        author_year_pairs = list(
            filter(
                lambda x: x != None, map(process_citations, cleaned_in_text_citations)
            )
        )
        references_dictionary = find_citation_matches(
            author_year_pairs, references_clean, references_dictionary, location
        )

    references_df = pd.DataFrame(
        {k: [",".join(v)] for k, v in references_dictionary.items()}, index=["section"]
    ).T.reset_index(names="reference")
    return references_df


def clean_in_text_citations(in_text_citations):
    return [
        item
        for group in [
            re.sub(r"\(|\)|see also|’s", "", item).split(",")
            for item in in_text_citations
        ]
        for item in group
    ]


### DIFF
def text_preprocess_for_reference_matching(references_text):
    # START searching ONCE References tag found
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


### DIFF
def get_in_text_citations(text):
    IN_PARANTHESES_CITATION_REGEX = r"\([&\w\s., ]+\s\d{3,4}\)"
    AND_PATTERN = "\S+ & \S+ \(\d{3,4}\)"
    ONE_PATTERN = "[A-Z]\S+ \(\d{3,4}\)"
    ET_AL_PATTERN = "[A-Z][a-z] et al. \(\d{3,4}\)"
    IN_TEXT_CITATION_REGEX = (
        f"{IN_PARANTHESES_CITATION_REGEX}|{AND_PATTERN}|{ONE_PATTERN}|{ET_AL_PATTERN}"
    )
    return re.findall(IN_TEXT_CITATION_REGEX, text)


def process_citations(citation: str):
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


def find_citation_matches(author_year_pairs, full_references, data, location):
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


def convert_pdf_to_dataframes(doc):
    """Returns (sections_df, references_df)"""
    sections, sections_df = make_sections_dataframe(doc)
    references_df = make_references_dataframe(sections, sections_df)
    return sections_df, references_df


def sanitize_dataframe_for_download(df):
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = df[col].str.replace("\n", " ").str.replace('"', "'")
            except AttributeError:
                continue
    return df
