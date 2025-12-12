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
        async with httpx.AsyncClient(timeout=150.0) as client:
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
/* Global Base Styles */
.gradio-container {
    background: linear-gradient(135deg, #f2f9fc 0%, #FEEAC9 50%, #ffd3b6 100%) !important;
    min-height: 100vh !important;
    padding: 55px !important;
}

#chatbot {
    border-radius: 20px !important;
    border: 2px solid #FCF6D9 !important;
    box-shadow: 0 6px 25px rgba(76, 112, 64, 0.15) !important;
    background: linear-gradient(135deg, #f1f8f4 0%, #FCF6D9 100%) !important;
}

#title-text {
    text-align: center;
    background: linear-gradient(135deg, #FFCDC9 0%, #FD7979 50%, #e03434 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800 !important;
    letter-spacing: -0.5px !important;
}

#subtitle-text {
    text-align: center;
    color: #5d4037 !important;
    font-weight: 500 !important;
    opacity: 0.9;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.5 !important;
}

textarea {
    border-radius: 15px !important;
    border: 2px solid #ffffff !important;
    background: #ffffff !important;
    padding: 12px !important;
}

textarea:focus {
    border-color: #947b7b !important;
    box-shadow: 0 0 0 3px rgba(129, 199, 132, 0.15) !important;
    outline: none !important;
}

#send-btn {
    background: linear-gradient(135deg, #6e5656 0%, #5e4142 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    color: white !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    transition: all 0.3s ease !important;
}

#send-btn:hover {
    background: linear-gradient(135deg, #5e4142 0%, #382526 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2) !important;
}

#clear-btn {
    margin: 20px auto !important;
    border-radius: 15px !important;
    border: 3px solid #8d6e63 !important;
    color: #7a6058 !important;
    background: transparent !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

#clear-btn:hover {
    background: rgba(141, 110, 99, 0.1) !important;
    border-color: #5d4037 !important;
    transform: scale(1.03) !important;
}

.message.user {
    background: linear-gradient(135deg, #f0e9e9 0%, #e3dada 100%) !important;
    border-radius: 18px 18px 4px 18px !important;
    border: 3px solid #6b5152 !important;
}

.message.bot {
    background: linear-gradient(135deg, #f1fcd2 0%, #cff5ba 100%) !important;
    border-radius: 18px 18px 18px 4px !important;
    border: 3px solid #76ad58 !important;
}

/* Desktop/Tablet (Screen > 768px) */
@media (min-width: 769px) {
    /* Using global padding (55px) */
    
    #title-text {
        font-size: 2.8em !important;
        margin-bottom: 8px !important;
    }
    
    #subtitle-text {
        font-size: 1.15em !important;
    }
    
    textarea {
        font-size: 16px !important;
    }
    
    #send-btn {
        min-height: 48px !important;
    }
    
    #clear-btn {
        width: 60% !important;
    }
}

/* Mobile (Screen <= 768px) */
@media (max-width: 768px) {
    .gradio-container {
        padding: 0 !important;
        margin: 0 !important;
        overflow-x: hidden !important;
    }

    .block-container {
        width: 100% !important;
        max-width: 100% !important;
        padding: 5px !important;
        margin: 0 !important;
    }
    
    #chatbot {
        border-radius: 12px !important;
        height: 65vh !important;
        max-height: none !important;
        width: 100% !important;
        margin-bottom: 10px !important;
    }
    
    #title-text {
        font-size: 1.8em !important;
        margin-top: 5px !important;
        margin-bottom: 5px !important;
    }
    
    #subtitle-text {
        font-size: 0.95em !important;
        padding: 0 2px !important;
    }
    
    textarea {
        font-size: 16px !important;
        padding: 8px !important;
        border-radius: 10px !important;
    }
    
    #send-btn {
        min-height: 44px !important;
    }
    
    #clear-btn {
        width: 90% !important;
        margin: 10px auto !important;
    }
    
    .gradio-row {
        gap: 5px !important;
    }
}

/* Small Screen Mobile (<= 375px) */
@media (max-width: 375px) {
    #title-text {
        font-size: 1.5em !important;
    }
    
    #subtitle-text {
        font-size: 0.85em !important;
    }
    
    #chatbot {
        height: 60vh !important;
    }
}
'''

with gr.Blocks(title="Travel Assistant", theme=gr.themes.Soft(), css=custom_css) as demo:
    gr.HTML("<h1 id='title-text'> AI Travel Assistant</h1>")
    gr.HTML("<p id='subtitle-text'>Your dedicated travel assistant for structured, intelligent trip planning.<br>Designing clear, personalized trips just for you.</p>")
    
    session_id_state = gr.State(value=lambda: str(uuid.uuid4()))
    
    chatbot = gr.Chatbot(elem_id="chatbot", height=400, type='messages')
    
    with gr.Row():
        msg = gr.Textbox(label="", placeholder=" Where would you like to explore? (e.g., 'Plan a 2-day eco-tour in Kyoto, Japan')", scale=5, show_label=False)
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
        server_name="0.0.0.0", 
        server_port=7860
    )