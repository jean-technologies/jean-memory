"""
Jean Memory Python SDK - Example with OpenAI
Shows how to use Jean Memory context with your LLM
"""

import os
from openai import OpenAI
from jeanmemory import JeanClient

def main():
    # Initialize clients
    jean = JeanClient(api_key=os.environ.get("JEAN_API_KEY", "jean_sk_your_api_key_here"))
    openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Get user token (in production, this comes from your frontend OAuth flow)
    user_token = input("Enter your Jean Memory user token: ")
    
    print("\n🧠 Jean Memory Chatbot")
    print("Type 'quit' to exit\n")
    
    while True:
        # Get user input
        user_message = input("You: ").strip()
        
        if user_message.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not user_message:
            continue
        
        # Get context from Jean Memory
        context_response = jean.get_context(
            user_token=user_token,
            message=user_message
        )
        
        # Engineer your final prompt
        final_prompt = f"""
Using the following context, please answer the user's question.
The context is a summary of the user's memories related to their question.

Context:
---
{context_response.text}
---

User Question: {user_message}
"""
        
        # Call OpenAI with context
        completion = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": final_prompt}
            ]
        )
        
        print(f"\nAssistant: {completion.choices[0].message.content}\n")

if __name__ == "__main__":
    main()