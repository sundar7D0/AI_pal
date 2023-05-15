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
doc_url = tab1.text_input("Enter document URL", placeholder="https://docs.google.com/document/d/1KpdSKD8-Rn0bWPTu4UtK54ks0yv2j22pA5SrAD9av4s/edit")

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
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES, redirect_uri="https://sundar7d0-gptpal--gptpal-kq1rdk.streamlit.app")
            creds = flow.run_local_server(port=80)
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


def maine(document_id):
    """Uses the Docs API to print out the text of a document."""
    credentials = get_credentials()
    docs_service = build(serviceName="docs", version="v1", credentials=credentials)
    doc = docs_service.documents().get(documentId=document_id).execute()
    doc_content = doc.get("body").get("content")
    st.write("File contents: ")
    text_contents = read_structural_elements(doc_content)
    st.write(text_contents)
    st.write("\n Upserting the contents to pinecone...")
    import openai
    import pinecone
    # initialize connection to pinecone (get API key at app.pinecone.io)
    pinecone.init(
        api_key="1a7ccf41-091a-4567-862a-02b2513a77cb", #"f7167eee-6383-4eec-857e-91c402f13f3b",
        environment="us-east1-gcp"
    )
    embed_model = "text-embedding-ada-002"

    from langchain.embeddings.openai import OpenAIEmbeddings
    index_name = "langchain-demo"
    # check if 'openai' index already exists (only create index if not)
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(index_name, dimension=1536)
    
    embeddings = OpenAIEmbeddings()
    # connect to index
    from langchain.text_splitter import CharacterTextSplitter
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.vectorstores import Pinecone

    #text_splitter = CharacterTextSplitter(chunk_size=10, chunk_overlap=0)
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a really small chunk size, just to show.
        chunk_size = 500,
        chunk_overlap  = 100,
        length_function = len,
    )
    texts = text_splitter.create_documents([text_contents])
    docs = text_splitter.split_documents(texts)
    st.write("Splitted documents: ")
    st.write(docs)
    docsearch = Pinecone.from_documents(docs, embeddings, index_name=index_name)
    st.write("Done upserting!")

upsert = st.button("Upsert")

def upserter():
    if not doc_url:
        st.error('Please enter the GDrive URL that you want to upsert!')
        return
    document_id = re.search(r'document/d/([\w-]+)', doc_url)
    if document_id:
        document_id = document_id.group(2)
    else:
        st.error("Invalid Google Drive document link.")
        return
    with open("credentials.json", "w") as creds:
        creds.write(creds_str)
    with open("token.json", "w") as tok:
        tok.write(creds_str)
    maine(document_id)
    
if upsert:
    upserter()
    

# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
#st.button("Re-run")
