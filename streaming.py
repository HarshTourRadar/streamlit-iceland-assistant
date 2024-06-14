import streamlit as st
from openai import AssistantEventHandler, OpenAI
from typing_extensions import override

assistant_id = st.secrets["assistant_id"]
openai_client = OpenAI(api_key=st.secrets["openai_apikey"])


class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print("\nassistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)
        yield delta.value

    def on_tool_call_created(self, tool_call):
        print(f"\nassistant tool created > {tool_call.type}\n", flush=True)


# Display the chat history
def create_chat_area(chat_history):
    for chat in chat_history:
        role = chat["role"]
        with st.chat_message(role):
            st.write(chat["content"])


# Generate chat responses using the OpenAI API
def chat(messages, thread_id, stream=False):
    # completion = openai.chat.completions.create(
    #     model=model,
    #     messages=messages,
    #     max_tokens=max_tokens,
    #     temperature=temperature,
    #     n=n,
    #     stream=stream,
    # )
    # for chunk in completion:
    #     try:
    #         yield (
    #             chunk.choices[0].delta.content
    #             if chunk.choices[0].finish_reason != "stop"
    #             else ""
    #         )
    #     except Exception as e:
    #         yield f"error: {e.__traceback__}"

    print("===========", messages)
    try:
        openai_messages = openai_client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=messages[0]["content"],
        )

        runs = openai_client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            stream=True,
        )

        print("runs dict: ", runs.__dict__)

        for chunk in runs:
            print("-----------", chunk)
            print("***************", chunk.__dict__)
            try:
                yield (
                    chunk.choices[0].delta.content
                    if chunk.choices[0].finish_reason != "stop"
                    else ""
                )
            except Exception as e:
                yield f"error: {e}"

        # print("openai_messages: ", openai_messages)

        # with openai_client.beta.threads.runs.stream(
        #     thread_id=thread_id,
        #     assistant_id=assistant_id,
        #     event_handler=EventHandler(),
        # ) as stream:
        #     stream.until_done()
    except Exception as e:
        yield f"parent error: {e}"


# Main function to run the Streamlit app
def main():
    # Streamlit settings
    st.markdown(
        """<style>.block-container{max-width: 66rem !important;}</style>""",
        unsafe_allow_html=True,
    )
    st.title("TourRadar - Iceland tour assistant")
    st.markdown("---")

    # Session state initialization
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "streaming" not in st.session_state:
        st.session_state.streaming = False

    # API key setup
    openai_key = st.secrets["openai_apikey"]
    if openai_key is None:
        with st.sidebar:
            st.subheader("Settings")
            openai_key = st.text_input("Enter your OpenAI key:", type="password")
    elif openai_key:
        run_chat_interface()
    else:
        st.error("Please enter your OpenAI key in the sidebar to start.")


# Run the chat interface within Streamlit
def run_chat_interface():
    create_chat_area(st.session_state.chat_history)

    user_input = st.chat_input("How can I help you?")

    thread = openai_client.beta.threads.create()

    # Handle user input and generate assistant response
    if user_input or st.session_state.streaming:
        process_user_input(user_input=user_input, thread_id=thread.id)


def process_user_input(user_input, thread_id):
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        gpt_answer = chat(
            messages=st.session_state.chat_history, thread_id=thread_id, stream=True
        )
        st.session_state.generator = gpt_answer
        st.session_state.streaming = True
        st.session_state.chat_history.append({"role": "assistant", "content": ""})
        st.rerun()
        # st.experimental_rerun()
    else:
        update_assistant_response()


def update_assistant_response():
    try:
        chunk = next(st.session_state.generator)
        st.session_state.chat_history[-1]["content"] += chunk
        # st.experimental_rerun()
        st.rerun()
    except StopIteration:
        st.session_state.streaming = False
        # st.experimental_rerun()
        st.rerun()


if __name__ == "__main__":
    main()
