import streamlit as st
from openai import AssistantEventHandler, OpenAI
from typing_extensions import override

result_output = []


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


def format_image_html(url, width, height):
    return f'<br><img src="{url}" width="{width}" height="{height}">'


if __name__ == "__main__":
    st.markdown(
        """<style>.block-container{max-width: 66rem !important;}</style>""",
        unsafe_allow_html=True,
    )
    st.title("TourRadar - Iceland tour assistant")

    openai_client = OpenAI(api_key=st.secrets["openai_apikey"])
    assistant_id = st.secrets["assistant_id"]

    try:
        thread = openai_client.beta.threads.create()

        if "openai_model" not in st.session_state:
            st.session_state["openai_model"] = "gpt-3.5-turbo"

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("How can I help you?"):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                res_box = st.empty()
                res_box.markdown("Processing...")
                openai_messages = openai_client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=st.session_state.messages[-1]["content"],
                )

                with openai_client.beta.threads.runs.stream(
                    thread_id=thread.id,
                    assistant_id=assistant_id,
                    event_handler=EventHandler(),
                    instructions="If the user asks for images or itinerary, please fetch the accurate and precise images from the attached documents.",
                ) as stream:
                    stream.until_done()
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": stream._current_message_content.text.value,
                        }
                    )

        # Example of how to use format_image_html
        if "image_url" in st.session_state or "cdn.tourradar.com" in st.session_state:
            image_html = format_image_html(st.session_state["image_url"], 500, 500)
            st.markdown(image_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(e)
