import gradio as gr
import httpx
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

async def chat_function(message, history, session_id):
    if not message:
        yield "", history
        return

    history.append({"role": "user", "content": message})
    yield "", history

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {"message": message, "session_id": session_id}
            response = await client.post(f"{API_URL}/chat", json=payload)
            response.raise_for_status()
            result = response.json()
            bot_response_text = result.get("response", "Error: Empty response")
    except httpx.ConnectError:
        bot_response_text = "Error: Could not connect to backend"
    except httpx.TimeoutException:
        bot_response_text = "Error: Request timed out"
    except Exception as e:
        bot_response_text = f"Error: {str(e)}"

    history.append({"role": "assistant", "content": bot_response_text})
    yield "", history

custom_css = '''
/* 森系风格 (Nature/Forest Theme) */
/* 主容器 - 森林绿渐变背景 */
.gradio-container {
    background: linear-gradient(135deg, #f2f9fc 0%, #E7F2EF 50%, #ffd3b6 100%) !important;
    min-height: 100vh !important;
    padding: 80px !important;
}

/* 内容区 - 奶白色卡片 */
.main {
    max-width: 1400px !important;
    margin: 0 auto !important;
    background: rgba(255, 253, 248, 0.95) !important;
    border-radius: 30px !important;
    padding: 45px !important;
    box-shadow: 0 15px 50px rgba(76, 112, 64, 0.15) !important;
    border: 2px solid rgba(168, 230, 207, 0.3) !important;
}

/* 聊天框 - 柔和的森林色 */
#chatbot {
    border-radius: 20px !important;
    border: 2px solid #edf6fa !important;
    box-shadow: 0 6px 25px rgba(76, 112, 64, 0.1) !important;
    background: linear-gradient(135deg, #f1f8f4 0%, #fafdf8 100%) !important;
}

/* 标题 - 森林绿渐变 */
#title-text {
    text-align: center;
    background: linear-gradient(135deg, #6D94C5 0%, #66bb6a 50%, #81c784 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.8em !important;
    margin-bottom: 8px !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
}

/* 副标题 */
#subtitle-text {
    text-align: center;
    color: #5d4037 !important;
    font-size: 1.15em !important;
    font-weight: 400 !important;
    opacity: 0.85;
}

/* 输入框样式 */
.textbox textarea {
    border-radius: 15px !important;
    border: 2px solid #c8e6c9 !important;
    background: #fafdf8 !important;
    font-size: 16px !important;
    padding: 12px !important;
}

.textbox textarea:focus {
    border-color: #81c784 !important;
    box-shadow: 0 0 0 3px rgba(129, 199, 132, 0.15) !important;
    outline: none !important;
}

/* 发送按钮 - 森林绿 */
#send-btn {
    background: linear-gradient(135deg, #66bb6a 0%, #4caf50 100%) !important;
    border: none !important;
    border-radius: 15px !important;
    color: white !important;
    font-weight: 600 !important;
    min-height: 48px !important;
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important;
    transition: all 0.3s ease !important;
}

#send-btn:hover {
    background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4) !important;
}

/* 清除按钮 - 大地棕色边框 */
#clear-btn {
    border-radius: 15px !important;
    border: 2px solid #8d6e63 !important;
    color: #5d4037 !important;
    background: transparent !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

#clear-btn:hover {
    background: rgba(141, 110, 99, 0.1) !important;
    border-color: #5d4037 !important;
}

/* 消息气泡优化 */
.message.user {
    background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%) !important;
    border-radius: 18px 18px 4px 18px !important;
    border: 1px solid #a5d6a7 !important;
}

.message.bot {
    background: linear-gradient(135deg, #fff9c4 0%, #fff59d 100%) !important;
    border-radius: 18px 18px 18px 4px !important;
    border: 1px solid #fff59d !important;
}
'''

with gr.Blocks(title="Travel Agent", theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.HTML("<h1 id='title-text'> AI Travel Agent</h1>")
    gr.HTML("<p id='subtitle-text'> Your dedicated travel assistant for structured, intelligent trip planning. Designing clear, personalized trips just for you.</p>")
    
    session_id_state = gr.State(value=lambda: str(uuid.uuid4()))
    
    chatbot = gr.Chatbot(elem_id="chatbot", height=400)
    
    with gr.Row():
        msg = gr.Textbox(label="", placeholder=" Where would you like to explore? (e.g., 'Plan a 5-day eco-tour in Kyoto, Japan')", scale=5, show_label=False)
        submit_btn = gr.Button("Send ", elem_id="send-btn", scale=1)
    
    clear_btn = gr.Button(" Clear Chat & New Journey", elem_id="clear-btn")

    msg.submit(fn=chat_function, inputs=[msg, chatbot, session_id_state], outputs=[msg, chatbot], queue=True)
    submit_btn.click(fn=chat_function, inputs=[msg, chatbot, session_id_state], outputs=[msg, chatbot], queue=True)
    
    def clear_chat():
        return [], str(uuid.uuid4())
    
    clear_btn.click(fn=clear_chat, inputs=None, outputs=[chatbot, session_id_state], queue=False)

# Run with:
# gradio src/carribulus/ui/app.py
if __name__ == "__main__":
    demo.queue()
    demo.launch(
        server_name="localhost", 
        server_port=7860
    )