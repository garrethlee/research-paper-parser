import streamlit as st


def set_converted_state(state):
    """
    Set the state of the "convert_clicked" key in the session state dictionary.

    Parameters:
    - state: The new state to set for the "convert_clicked" key.

    Returns:
    None
    """
    st.session_state["convert_clicked"] = state


def save_editor_changes():
    """
    Save the editor changes made to the PDF dataframe.

    Parameters:
    None

    Returns:
    None
    """
    pdf_dataframe = st.session_state["pdf_dataframe"]
    updates = st.session_state["pdf_editor"]["edited_rows"]
    # Save the updated dataframe in the session state
    for idx, journal_dict in updates.items():
        for key in journal_dict:
            journal = journal_dict[key]
        pdf_dataframe.at[idx, "Journal"] = journal

    pdf_to_journal_records = pdf_dataframe.to_dict(orient="records")
    # Update the session state's pdf-to-journal matches
    for record in pdf_to_journal_records:
        filename, journal = list(record.values())
        st.session_state["pdf_to_journal_map"][filename] = journal


def create_pdf_dataframe(pdf_files):
    """
    Create a pandas DataFrame from a list of PDF files.

    Parameters:
        pdf_files (list): A list of PDF files.

    Returns:
        pdf_dataframe (pandas.DataFrame): A DataFrame containing the filenames and journals of the PDF files.
    """
    import pandas as pd
    if "pdf_to_journal_map" not in st.session_state:
        st.session_state["pdf_to_journal_map"] = {}

    pdf_file_names = []
    journals = []

    # Check session state for any available values
    for pdf_file in pdf_files:
        filename = pdf_file.name
        journal = st.session_state["pdf_to_journal_map"].get(filename, None)

        pdf_file_names.append(filename)
        journals.append(journal)

    pdf_dataframe = pd.DataFrame(
        {"Filename": pdf_file_names, "Journal": journals})

    # Save current dataframe in session state
    st.session_state['pdf_dataframe'] = pdf_dataframe

    return pdf_dataframe
