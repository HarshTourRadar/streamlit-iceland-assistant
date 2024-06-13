import streamlit as st
from openai import AssistantEventHandler, OpenAI
from typing_extensions import override

assistant_id = st.secrets["assistant_id"]
openai_client = OpenAI(api_key=st.secrets["openai_apikey"])

result_output = []

if "user_input" not in st.session_state:
    st.session_state.user_input = ""


def submit():
    st.session_state.user_input = st.session_state.query
    st.session_state.query = ""


class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print("\nassistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        result_output.append(delta.value)
        result = "".join(result_output).strip()
        res_box.markdown(result, unsafe_allow_html=True)
        print(delta.value, end="", flush=True)

    def on_tool_call_created(self, tool_call):
        print(f"\nassistant tool created > {tool_call.type}\n", flush=True)


if __name__ == "__main__":
    st.title("TourRadar - Iceland tour assistant")
    st.text_input("How can I help you?: ", key="query", on_change=submit)
    user_input = st.session_state.user_input
    st.write("You entered: ", user_input)

    my_assistant = openai_client.beta.assistants.retrieve(assistant_id)
    thread = openai_client.beta.threads.create()

    if user_input:
        st.markdown("----")
        res_box = st.empty()
        res_box.markdown("Processing...")

        message = openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input,
        )

        with openai_client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant_id,
            event_handler=EventHandler(),
        ) as stream:
            stream.until_done()

        st.markdown("----")
