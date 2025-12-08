from litellm import completion
import os
from typing import List
from .models import Message

def generate_rolling_summary(current_summary: str, new_messages: List[Message]) -> str:
    """
    Condenses the current summary and new messages into a new summary.
    Uses a synchronous call for simplicity, but could be async if needed.
    """
    if not new_messages:
        return current_summary

    # Format new messages for the prompt
    new_messages_text = "\n".join([f"{m.role}: {m.content}" for m in new_messages])

    prompt = f"""
    You are a helpful assistant summarizing a conversation.
    
    Current Summary:
    {current_summary}
    
    New Messages:
    {new_messages_text}
    
    Update the summary to include the key points from the new messages. 
    Keep it concise but retain important details for context.
    """

    # Use a lightweight model for summarization if possible
    model = os.getenv("SUMMARY_MODEL")

    try:
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating summary: {e}")
        return current_summary
