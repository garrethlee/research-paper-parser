import re
import pandas as pd

ABSTRACT_KEY = ("AdvPSA35F", 10.0)
HEADERS_KEY = ("AdvP2A83", 10.0)


def make_sections_dataframe(doc):
    text_nest = get_sections(doc)
    sections_df = pd.DataFrame(text_nest, index=["text"]).T
    sections_df.name = doc.name
    return text_nest, sections_df


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


def process_citations(citation_group: str):
    citations = citation_group.split(";")
    results = []
    for citation in citations:
        try:
            # case 1: &
            if " and " in citation:
                tokens = citation.split(",")
                year = tokens[-1]
                names = ",".join(tokens[:-1])
                names = names.replace(" and ", ",")
                names_split = names.split(",")
                results.append(
                    (
                        [
                            name.strip()
                            for name in names_split
                            if name.strip() not in ("", "e.g.")
                        ],
                        year.strip(),
                    )
                )

            # case 2: et al
            if "et al." in citation:
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
                    results.append(([author], year[1:-1]))
                else:
                    citation_split = citation.split(",")
                    results.append(([citation_split[-2]], citation_split[-1]))
        except:
            results.append(([""], ""))

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


def make_references_dataframe(text_nest, sections_df):
    references_dictionary = {}
    references_clean = text_preprocess_for_reference_matching(text_nest["REFERENCES"])
    for location, text in zip(sections_df.index[:-1], sections_df.values[:-1]):
        # print(location, "\n")
        in_text_citations = get_in_text_citations(text.item())
        # print(in_text_citations)
        cleaned_in_text_citations = [
            citation if citation[0] != "(" else citation[1:-1]
            for citation in in_text_citations
        ]
        author_year_pairs_nested = list(
            filter(
                lambda x: x != None, map(process_citations, cleaned_in_text_citations)
            )
        )
        author_year_pairs = [
            item for group in author_year_pairs_nested for item in group
        ]
        references_dictionary = find_citation_matches(
            author_year_pairs, references_clean, references_dictionary, location
        )
        # print()

    references_df = pd.DataFrame(
        {k: [",".join(v)] for k, v in references_dictionary.items()}, index=["section"]
    ).T.reset_index(names="reference")
    return references_df


def get_in_text_citations(text):
    IN_PARANTHESES_CITATION_REGEX = r"\([&\w\s.,\-; ]+\s\d{3,4}\)"
    AND_PATTERN = "\S+ and \S+ \(\d{3,4}\)"
    ONE_PATTERN = "[A-Z]\S+ \(\d{3,4}\)"
    ET_AL_PATTERN = "[A-Z][a-z] et al. \(\d{3,4}\)"
    IN_TEXT_CITATION_REGEX = (
        f"{IN_PARANTHESES_CITATION_REGEX}|{AND_PATTERN}|{ONE_PATTERN}|{ET_AL_PATTERN}"
    )
    return re.findall(IN_TEXT_CITATION_REGEX, text)


def convert_pdf_to_dataframes(doc):
    """Returns (sections_df, references_df)"""
    sections, sections_df = make_sections_dataframe(doc)
    references_df = make_references_dataframe(sections, sections_df)
    return sections_df, references_df


def structure_doc_by_size_and_font(doc):
    # first_page_fonts = {}
    rest_fonts = {}
    seqs = []
    prev_size, prev_font = 0, 0
    for page in doc:
        d = page.get_text("dict")
        blocks = d["blocks"]
        for block in blocks:
            if "lines" in block.keys():
                spans = block["lines"]
                for span in spans:
                    data = span["spans"]
                    for lines in data:
                        cur_size = round(lines["size"], 2)
                        cur_font = lines["font"].split("+")[0]

                        key = (cur_font, cur_size)
                        # print(lines['text'], key)

                        if cur_size == prev_size and cur_font == prev_font:
                            latest_item = rest_fonts[key][-1]

                            # if page.number == 0:
                            # first_page_fonts[key][-1] = latest_item + " " + lines['text']

                            rest_fonts[key][-1] = latest_item + " " + lines["text"]
                            seqs[-1] = seqs[-1] + " " + lines["text"]

                        else:
                            # if page.number == 0:
                            # first_page_fonts[key] = first_page_fonts.get(key, []) + [lines['text']]
                            rest_fonts[key] = rest_fonts.get(key, []) + [lines["text"]]
                            seqs.append(lines["text"])

                        prev_size = cur_size
                        prev_font = cur_font

    # sorted_first_page_fonts = dict(sorted(first_page_fonts.items(), key = lambda x: x[0][1], reverse = True))
    sorted_rest_fonts = sorted(rest_fonts.items(), key=lambda x: x[0][1], reverse=True)
    return seqs, sorted_rest_fonts


def get_headers(fonts):
    """Returns list of text (headers) that has size equal to AOM-standard headers"""
    first_part = []
    second_part = []
    for key, val in fonts:
        if key == ABSTRACT_KEY:
            first_part = val
        if key == HEADERS_KEY:
            second_part = val
    return first_part[:2] + second_part + first_part[2:]


def find_earliest_uppercase_index(s):
    for i, char in enumerate(s):
        if char.isalpha() and char.upper() == char:
            return i
    return len(s)


def get_text_nest(seqs, starting_text_nest, pdf_headers):
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
                starting_text_nest[cur_header] = (
                    starting_text_nest.get(cur_header, "") + " " + intro_part
                )
            else:
                starting_text_nest[cur_header] = (
                    starting_text_nest.get(cur_header, "") + " " + sequence
                )

    return starting_text_nest


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
