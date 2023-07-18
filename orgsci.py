import fitz
import re
import pandas as pd
from section import Section


### DIFF
def get_sections(doc):
    main_section = Section("", 100)

    prev_size = 100
    curr_section = main_section

    for page in doc:
        rect = fitz.Rect(
            page.rect.x0 + 40, page.rect.y0 + 60, page.rect.x1 - 40, page.rect.y1 - 40
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


### DIFF
def preprocess_sections(sections):
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
        if len(section.content) > 100:
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
    # Preprocess sections
    abstract_section = Section("Abstract. ", 0)

    abstract_index = sections.index(abstract_section)
    abstract_text = sections.pop(abstract_index + 1)
    sections[abstract_index].add_child(abstract_text)

    sections = sections[abstract_index:]

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

    # Add keywords to sections
    abstract_text = sections_df.iloc[0].item()
    abstract, keywords = abstract_text.split("Keywords")
    cleaned_keywords = [keyword.strip() for keyword in keywords.split("•")]
    new_row = pd.DataFrame({"text": str(cleaned_keywords)}, index=["Keywords"])
    sections_df = pd.concat([new_row, sections_df])

    sections_df.name = doc.name
    return sections, sections_df


### DIFF
def make_references_dataframe(sections, sections_df):
    references_dictionary = {}
    references_text = sections[-1].print_contents()
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
            [
                c.strip()  # Remove whitespace
                for c in citation[1:-1].split(",")  # Remove '(' and ')'
                if any(char.isdigit() for char in c)
            ]  # Remove any that doesn't have digits (year)
            for citation in in_text_citations
        ]
        for item in group
    ]


### DIFF
def text_preprocess_for_reference_matching(references_text):
    # START searching ONCE References tag found
    references_dirty = re.sub("\n", " ", references_text)
    references_dirty = " ".join(references_dirty.split())
    references = re.sub("([0-9]|html|\))\s?\.", r"\g<0>\n", references_dirty)

    # Make list of references
    pattern = r"[A-ZÆØÅæøå][ÆØÅæøåA-Za-z]+.*[A-Z]{1,3},? .*\(\d{4}\).*[html|\d|\)]\."
    references_clean = re.findall(pattern, references)
    return references_clean


### DIFF
def get_in_text_citations(text):
    IN_TEXT_CITATION_REGEX = r"\([\w\s.,]+\s\d{3,4}\s?\)"
    return re.findall(IN_TEXT_CITATION_REGEX, text)


### DIFF
def process_citations(citation: str):
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


### DIFF
def find_citation_matches(author_year_pairs, full_references, data, location):
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


### SAME
def convert_pdf_to_dataframes(path):
    """Returns (sections_df, references_df)"""
    sections, sections_df = make_sections_dataframe(path)
    references_df = make_references_dataframe(sections, sections_df)
    return sections_df, references_df


### SAME
def sanitize_dataframe_for_download(df):
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = df[col].str.replace("\n", " ").str.replace('"', "'")
            except AttributeError:
                continue
    return df
