import streamlit as st
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
import openai
from llama_index import SimpleDirectoryReader

# st.set_page_config(page_title="LibelChat",layout="centered", initial_sidebar_state="auto", menu_items=None)
st.set_page_config(page_title="LibelChat", page_icon=":fireworks:", layout="wide", initial_sidebar_state="expanded")

# ----------------------- Set up sidebar -------------------------

guidance_template = """
Act as a legal expert with more than 20 years experience of representing claimants. Your task is to prepare a Statement of Case in a form suitable to present to a court for an initial hearing. It is very important that your responses are tailored to reflect the details you are given.
"""

with st.sidebar:

    st.title("LibelChat Test Harness")

    st.write("This 'test harness' allows questions to be batched and responses generated automatically. ")

    st.write("Instructions for use are as follows:")

    st.markdown("""
    1. Prepare your questions in plain text format, one question per file, and place them in the 'questions' directory.
    2. Ensure that the RAG data for ingestion is included in the 'data' directory. The default data set is comprised of the Westlaw 'serious harm' cases and the Defamatory Act 2013 statute. Files can be added or removed as required.
    2. Adjust the settings in this side panel as required to determine the LLM model which will be used and its tempature setting. 
    3. Modify the LLM "system guidance" in the central panel if you wish. 
    3. Click on the Generate Results button to process the questions.
    4. Inspect the output and extract to an external file if required. This file will be directed to your Downloads folder.
    """)

    # Add model selection input field to the sidebar
    selected_model = st.selectbox("Select the model you would like to use:", ["gpt-3.5-turbo", "gpt-3.5-turbo-0613", "gpt-4", "gpt-4-0613", "Mistral"], key="selected_model", help="For OpenAPI, the 0613 models are updated and more steerable versions. See [this post](https://openai.com/blog/function-calling-and-other-api-updates) for further details.")
    
    # Add OpenAI API key input field to the sidebar
    openai_api_key = st.text_input("Enter your API key for the model you have selected", type="password", value="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", help="In the case of OpenAI you can find the API key on the [OpenAI dashboard](https://platform.openai.com/account/api-keys).")

    # Set the "temperature" for the LLM you have chosen
    selected_model = st.text_input("Set the temperature for the LLM you have chosen", key="llm_temperature", value=8.0, help="Temperature is a parameter that controls the randomness of the text generated by GPT. A lower temperature will result in more predictable output, while a higher temperature will result in more random output. The temperature parameter is set between 0 and 1, with 0 being the most predictable and 1 being the most random1. For transformation tasks, prefer a temperature of 0 or up to 0.3, while for writing tasks, you should juice the temperature higher, closer to 0.53. OpenAI models are non-deterministic, meaning that identical inputs can yield different outputs. Setting temperature to 0 will make the outputs mostly deterministic, but a small amount of variability may remain.")

    data_choice = st.selectbox("Choose source data:", ["RAG Only", "LLM only", "Both RAG and LLM"],  key="data_choice", help="help")

    new_guidance = st.text_area(label=":blue[The default prompt guidance is shown in the box below. It can be amended by you for testing purposes.]", height=200, key="guidance", value=guidance_template)


openai.api_key = "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"
st.title("LibelChat 💬")

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant",
            "content": "Ask me a question about libel law in the UK and Ireland"}
    ]

# --------------- Load RAG data -------------------------

@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Loading and indexing the legal docs – hang tight! This should take 1-2 minutes."):
        reader = SimpleDirectoryReader(
            #   input_dir="./data/Statutes", recursive=True)
            # input_dir="./data", recursive=True)
            input_dir="./data", recursive=True)
        docs = reader.load_data()
        service_context = ServiceContext.from_defaults(llm=OpenAI(
            model="gpt-3.5-turbo", temperature=0.5, system_prompt="Act as a UK qualified lawyer specialising in defamation. Use the provided Statute (the Defamation Act 2013) and details of legal cases (including judgments) to answer the questions put to you. Keep your answers technical and based on facts – do not hallucinate features. Cite the primary douments on which your answers are based. Note that 'DA' is an abbreviation for 'Defamation Act'"))
        index = VectorStoreIndex.from_documents(
            docs, service_context=service_context)
        st.write('Loaded ', len(docs),  ' documents')
        # st.write(docs)
        return index

index = load_data()

# ------------------------ Invoke chat ------------------

if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_question", verbose=True)

# Prompt for user input and save to chat history
if prompt := st.chat_input("Your question"):
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:  # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.chat_engine.chat(prompt)
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            # Add response to message history
            st.session_state.messages.append(message)