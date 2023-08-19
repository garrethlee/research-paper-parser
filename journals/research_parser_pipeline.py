import pandas as pd
import fitz
import regex as re


class ResearchParserPipeline:
    """
    A class for parsing research documents to extract sections and references information.

    This class provides methods to extract structured information from research documents,
    including sections and references data.

    Attributes:
        journal (str): The journal associated with the research document.
        doc_name (str): The name of the document being processed.

    Methods:
        get_sections_dataframe(doc: fitz.Document) -> pandas.DataFrame:
            Extracts sections from the input document and returns them as a DataFrame.

        get_references_dataframe(text_nest: dict, sections_df: pandas.DataFrame) -> pandas.DataFrame:
            Processes in-text citations and matches them to references, returning a DataFrame of references.

    Private Methods:
        _text_structure(input_doc):
            Extracts the text structure from the input document.

        _text_nest(input_structure, **kwargs):
            Organizes the text structure into a nested format.

        _section_dataframe(text_nest):
            Converts the nested text structure into a DataFrame of sections.

        _reference_preprocessor(input_obj):
            Preprocesses references for matching.

        _in_text_citations(text, in_parantheses_citation_regex):
            Extracts in-text citations from a given text.

        _in_text_citation_preprocessor(in_text_citations):
            Preprocesses in-text citations.

        _citation_reference_matcher(location, in_text_citations, reference_list, result_dictionary):
            Matches in-text citations to references.

        _reference_dataframe(reference_dictionary):
            Converts the reference dictionary into a DataFrame.
    """

    def __init__(self, journal):
        self.journal = journal
        self.doc_name = ""

    ### SECTIONS DATAFRAME
    def get_sections_dataframe(self, doc: fitz.Document):
        """
        Get the sections dataframe from the given input document.

        Parameters:
            input_doc (str): The input document from which to extract the sections.

        Returns:
            pandas.DataFrame: The dataframe containing the sections extracted from the input document.
        """
        self.doc_name = doc.name

        text_structure = self._text_structure(doc)
        text_nest = self._text_next(text_structure)
        section_dataframe = self._section_dataframe(text_nest)
        return section_dataframe

    def _text_structure(self, input_doc):
        pass

    def _text_nest(self, input_structure, **kwargs):
        pass

    def _section_dataframe(self, text_nest):
        sections_df = pd.DataFrame(text_nest, index=["text"]).T
        sections_df.name = self.doc_name
        return text_nest, sections_df

    ### REFERENCES DATAFRAME
    def get_references_dataframe(
        self, text_nest: dict, sections_df: pd.DataFrame
    ) -> pd.DataFrame:
        references_dictionary = {}
        processed_references = self._reference_preprocessor(text_nest)
        for location, text in zip(sections_df.index, sections_df.values):
            in_text_citations = self._in_text_citations(text)
            processed_in_text_citations = self._in_text_citation_preprocessor(
                in_text_citations
            )
            references_dictionary = self._citation_reference_matcher(
                location=location,
                in_text_citations=processed_in_text_citations,
                reference_list=processed_references,
                result_dictionary=references_dictionary,
            )
        references_dataframe = self._reference_dataframe(references_dictionary)
        return references_dataframe

    def _reference_preprocessor(self, text_nest):
        """
        Preprocesses the given text_nest by removing newline characters and extra spaces from the references_text. Then, extracts references from the cleaned references_text using a regular expression pattern. The extracted references are then further processed to split them into individual references. The final list of cleaned references is returned.

        Parameters:
        - text_nest: A list of strings representing the text nest to be preprocessed.

        Returns:
        - references_clean: A list of strings containing the cleaned and processed references extracted from the text_nest.
        """
        references_text = self._reference_from_text_nest(text_nest)
        references = " ".join(re.sub("\n", " ", references_text).split())
        reference_regex_pattern = r"(?:[\p{L}][\p{L}\s]+,(?:(?:\s|\-)[A-Z]\.){1,3}(?:,(?: . . .)?\s(?:&\s?)?)?)+ \(\d{4}\)"

        references_clean = re.findall(reference_regex_pattern, references)

        for idx, ref in enumerate(references_clean):
            # Last reference takes all text (until the end)
            if idx == len(references_clean) - 1:
                references_clean[idx] = references[references.find(ref) :]
            else:
                next_ref = references_clean[idx + 1]
                references_clean[idx] = references[
                    references.find(ref) : references.find(next_ref)
                ]

        return references_clean

    def _reference_from_text_nest(self, text_nest):
        """Implemented by the user"""
        pass

    def _in_text_citations(self, text, in_parantheses_citation_regex):
        """
        Generate a list of in-text citations from the given text using the specified in-parentheses citation regex pattern.

        Parameters:
            text (str): The text to search for in-text citations.
            in_parantheses_citation_regex (str): The regex pattern to match in-parentheses citations.

        Returns:
            list: A list of in-text citations found in the text.
        """
        IN_PARANTHESES_CITATION_REGEX = in_parantheses_citation_regex
        AND_PATTERN = "\S+ and \S+ \(\d{3,4}\)"
        ONE_PATTERN = "[A-Z]\S+ \(\d{3,4}\)"
        ET_AL_PATTERN = "[A-Z][a-z] et al. \(\d{3,4}\)"
        IN_TEXT_CITATION_REGEX = f"{IN_PARANTHESES_CITATION_REGEX}|{AND_PATTERN}|{ONE_PATTERN}|{ET_AL_PATTERN}"
        return re.findall(IN_TEXT_CITATION_REGEX, text)

    def _in_text_citation_preprocessor(self, in_text_citations):
        """
        Preprocesses the in-text citations by cleaning and formatting them.

        Parameters:
            in_text_citations (list): A list of in-text citations to be preprocessed.

        Returns:
            list: The preprocessed and formatted in-text citations.
        """
        cleaned_in_text_citations = self._clean_in_text_citations(in_text_citations)
        formatted_in_text_citations = self._format_in_text_citations(
            cleaned_in_text_citations
        )
        return formatted_in_text_citations

    def _clean_in_text_citations(self, in_text_citations):
        """Clean in-text citations and output consistent structure for formatting"""

    def _format_in_text_citations(self, cleaned_in_text_citations):
        """
        Processes a group of citations and returns a list of processed results.

        Parameters:
        citation_group (str): The input string containing a group of citations separated by ';'.

        Returns:
        list: A list of tuples, where each tuple contains a list of author names and the corresponding year of the citation.
        """
        citations = cleaned_in_text_citations.split(";")
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
                if "et al." in citation:
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
                        results.append(([author.split()[-1]], year[1:-1]))
                    else:
                        citation_split = citation.split(",")
                        results.append(
                            (
                                [citation_split[-2].split()[-1]],
                                citation_split[-1].split(":")[0],
                            )
                        )
            except:
                results.append(([""], ""))

        # Unnest the results
        return [item for group in results for item in group]

    def _reference_dataframe(self, reference_dictionary):
        """
        Generates a reference dataframe based on the given reference dictionary.

        Parameters:
            reference_dictionary (dict): A dictionary containing citation locations as keys and their respective citation references as values.

        Returns:
            references_df (pandas.DataFrame): The generated reference dataframe. The dataframe contains two columns: 'section' and 'reference', with 'section' as the index.
        """
        references_df = pd.DataFrame(
            # comma separated citation locations
            {k: [",".join(v)] for k, v in reference_dictionary.items()},
            index=["section"],
        ).T.reset_index(names="reference")

        return references_df
