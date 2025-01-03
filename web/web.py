import gradio as gr
from src.ai_doc_chat.chat import chat


with gr.Blocks() as demo:
    gr.Markdown("# Chat with Docs")
    chatbot = gr.Chatbot(type="messages")

    msg = gr.Textbox()
    clear = gr.Button("Clear")

    def user(user_message, history: list):
        return "", history + [{"role": "user", "content": user_message}]

    async def bot(history: list):
        history.append({"role": "assistant", "content": ""})
        async for character in chat(query=history[-2]["content"]):
            history[-1]["content"] += character
            yield history

    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear.click(lambda: None, None, chatbot, queue=False)

demo.launch()
