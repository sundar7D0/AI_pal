import os
import sys

import streamlit as st

# get file dir and add it to sys.path
cwd = os.path.dirname(os.path.realpath(__file__))
sys.path.append(cwd)

from langchain.chat_models import ChatOpenAI

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler

from utils.tools import ALL_TOOLS

st.set_page_config(
    page_title='GPTpal',
    page_icon='⚡',
    layout='wide',
    initial_sidebar_state='auto',
)

st.sidebar.markdown('')
openai_token = st.sidebar.text_input(
    'Enter your OpenAI API key:', placeholder='sk-...', type='password'
)

# Type your question
question = st.text_input(
    'Type your question:', placeholder="How to increase my company's revenue?"
)

selected_tools = st.sidebar.multiselect('Plugins:', ALL_TOOLS)
selected_params = {}

for tool in selected_tools:
    api = ALL_TOOLS[tool]['api']
    selected_params[tool] = {}
    selected_params[tool]['api'] = api

    if len(ALL_TOOLS[tool]['args']) > 0:
        st.sidebar.write(f'`{tool}` parameters:')

        for param in ALL_TOOLS[tool]['args']:
            param_value = st.sidebar.text_input(
                'label',
                key=f'{tool}_{param}',
                label_visibility='collapsed',
                placeholder=param,
                type='password',
            )
            selected_params[tool][param] = param_value

submit = st.button('Submit')


placeholder = st.empty()


def main():
    if submit:
        if not openai_token:
            st.error('Please enter your OpenAI token')
            return

        if not question:
            st.error('Please enter your question')
            return

        if not selected_tools:
            st.error('Please select at least one option')
            return

        # if params are not provided for a tool, then don't run
        for tool in selected_tools:
            if len(ALL_TOOLS[tool]) > 0:
                for param in ALL_TOOLS[tool]['args']:
                    if not selected_params[tool][param]:
                        st.error(f'Please enter `{param}` for `{tool}`')
                        return

        with st.spinner(text="Running GPTpal..."):
            os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
            #os.environ["OPENAI_API_KEY"] = openai_token
            chat = ChatOpenAI(streaming=True, callbacks=[MyCustomHandler()], temperature=0)
            messages = [
              SystemMessage(content="You are a helpful assistant that has access to many tools!"),
              HumanMessage(content=question) #("Who won the US open 2020 tennis? Tell their nationalities and spouses")
            ]
            from langchain.vectorstores import Pinecone
            from langchain.embeddings.openai import OpenAIEmbeddings
            index_name = "langchain_demo"
            embeddings = OpenAIEmbeddings()
            docsearch = Pinecone.from_existing_index(index_name, embeddings)
            docs = docsearch.similarity_search(query)
            st.write("Retrieved docs: ")
            st.write(docs)
            response = chat(messages)
            
        
class MyCustomHandler(BaseCallbackHandler):
    def __init__(self) -> None:
            self.response = []
            super().__init__()
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.response.append(token)
        result = "".join(self.response).strip()   
        placeholder.markdown(f"**:blue[{result}]**",unsafe_allow_html=True)
        #st.text_area(label ="",value=result, height =100)
        ##res_box.markdown(f'{result}') 
        #st.write(f"Custom handler, token: {token}")



if __name__ == '__main__':
    main()
