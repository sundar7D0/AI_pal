import os
import sys

import streamlit as st

# get file dir and add it to sys.path
cwd = os.path.dirname(os.path.realpath(__file__))
sys.path.append(cwd)

from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from utils.tools import ALL_TOOLS

st.set_page_config(
    page_title='GPTpal',
    page_icon='⚡',
    layout='wide',
    initial_sidebar_state='auto',
)

st.sidebar.markdown('## OpenAI Token')
openai_token = st.sidebar.text_input(
    'Enter your OpenAI token:', placeholder='sk-...', type='password'
)

# Type your question
question = st.text_input(
    'Type your question:', placeholder="How does the company's financials look like?"
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
            chat = ChatOpenAI(temperature=0)
            messages = [
              SystemMessage(content="You are a helpful assistant that has access to many tools!"),
              HumanMessage(content=question)
            ]
            result = chat(messages)
            

        st.write(result)

        # Optionally show the chain of thought, if user expands the subsection
        #with st.expander('See chain of thought'):
        #    st.write(chain_of_thought, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
