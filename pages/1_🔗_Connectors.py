import streamlit as st
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]


# The ID of a sample document.
DOCUMENT_ID = "1D9_izhimrk622JhQcNzVlgDfxz_b9is9KfcCDh_psFE"

st.set_page_config(page_title="🔗Connectors", page_icon="🔗")


#display progress for upsering
#progress_bar = st.sidebar.progress(0)

tab1, tab2 = st.tabs(["📂 GDrive", "📝 Notion"])

       


tab1.subheader("GDrive connector")
creds_str = tab1.text_input(
    "Enter contents of your 'credentials.json'", placeholder='{"installed": {"client_id": "...'
)

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth 2.0 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=9988)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def read_paragraph_element(element):
    """Returns the text in the given ParagraphElement.

    Args:
        element: a ParagraphElement from a Google Doc.
    """
    text_run = element.get("textRun")
    if not text_run:
        return ""
    return text_run.get("content")


def read_structural_elements(elements):
    """Recurses through a list of Structural Elements to read a document's text where text may be
    in nested elements.

    Args:
        elements: a list of Structural Elements.
    """
    text = ""
    for value in elements:
        if "paragraph" in value:
            elements = value.get("paragraph").get("elements")
            for elem in elements:
                text += read_paragraph_element(elem)
        elif "table" in value:
            # The text in table cells are in nested Structural Elements and tables may be
            # nested.
            table = value.get("table")
            for row in table.get("tableRows"):
                cells = row.get("tableCells")
                for cell in cells:
                    text += read_structural_elements(cell.get("content"))
        elif "tableOfContents" in value:
            # The text in the TOC is also in a Structural Element.
            toc = value.get("tableOfContents")
            text += read_structural_elements(toc.get("content"))
    return text


def maine():
    """Uses the Docs API to print out the text of a document."""
    st.write("calling get_credentials")
    credentials = get_credentials()
    st.write("calling docs_service")
    docs_service = build(serviceName="docs", version="v1", credentials=credentials)
    doc = docs_service.documents().get(documentId=DOCUMENT_ID).execute()
    doc_content = doc.get("body").get("content")
    st.write(read_structural_elements(doc_content))

upsert = st.button("Upsert")

if upsert:
    with open("tokens.json", "w") as creds:
        creds.write(creds_str)
    maine()
# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")
