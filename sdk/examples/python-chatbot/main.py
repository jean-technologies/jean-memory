"""
Jean Memory SDK Demo - Python Chatbot
5-line integration example using Jean Memory Python SDK
"""

from jeanmemory import JeanAgent

def main():
    # 🎯 5-line Jean Memory integration
    agent = JeanAgent(
        api_key="jean_sk_gdy4KGuspLZ82PHGI_3v8hEkP2iyFN4axYciKX8WqeA",
        system_prompt="You are a helpful tutor with access to the student's learning history.",
        modality="chat"
    )
    agent.run()

if __name__ == "__main__":
    main()