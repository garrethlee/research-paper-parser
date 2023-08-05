import regex as re
import traceback

import pandas as pd
from loguru import logger


def structure_doc_by_size_and_font(doc):
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
    HEADER_KEY = ("Times-Bold", 10.0)
    try:
        return fonts[HEADER_KEY]
    except KeyError as e:
        logger.error(f"Error occurred in 'get_headers': {traceback.format_exc()}")
        raise Exception(f"Error occurred in 'get_headers': {traceback.format_exc()}")


def get_text_nest(seqs, starting_text_nest, pdf_headers):
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


def find_earliest_uppercase_index(s):
    for i, char in enumerate(s):
        if char.isalpha() and char.upper() == char:
            return i
    return len(s)


def get_sections(doc):
    seqs, fonts = structure_doc_by_size_and_font(doc)
    pdf_headers = get_headers(fonts)
    text_nest = get_text_nest(seqs, {}, pdf_headers)
    return text_nest


def make_sections_dataframe(doc):
    text_nest = get_sections(doc)
    sections_df = pd.DataFrame(text_nest, index=["text"]).T
    sections_df.name = doc.name
    return text_nest, sections_df


def find_citation_matches(author_year_pairs, full_references, data, location):
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


def process_citations(citation_group: str):
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


def remove_prefix(citation):
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


def make_references_dataframe(text_nest, sections_df):
    references_dictionary = {}

    references_clean = text_preprocess_for_reference_matching(sections["References"])
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
        {k: [",".join(v)] for k, v in references_dictionary.items()}, index=["section"]
    ).T.reset_index(names="reference")
    return references_df


def get_in_text_citations(text):
    IN_PARANTHESES_CITATION_REGEX = "\([&\w\\.\s,\-; ]+\s\d{3,4}(?::\s\d{1,4})?\s\)"
    AND_PATTERN = "\S+ and \S+ \(\d{3,4}\)"
    ONE_PATTERN = "[A-Z]\S+ \(\d{3,4}\)"
    ET_AL_PATTERN = "[A-Z][a-z] et al. \(\d{3,4}\)"
    IN_TEXT_CITATION_REGEX = (
        f"{IN_PARANTHESES_CITATION_REGEX}|{AND_PATTERN}|{ONE_PATTERN}|{ET_AL_PATTERN}"
    )
    return re.findall(IN_TEXT_CITATION_REGEX, text)


def clean_in_text_citations(in_text_citations):
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


def convert_pdf_to_dataframes(doc):
    """Returns (sections_df, references_df)"""
    sections, sections_df = make_sections_dataframe(doc)
    references_df = make_references_dataframe(sections, sections_df)
    return sections_df, references_df
