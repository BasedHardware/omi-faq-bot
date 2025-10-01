import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

from core.llm import LLMService

async def main():
    
    try:
        llm = LLMService()
    except ValueError as e:
        print(f"Initialization Error: {e}")
        return

    print("\n--- Running End-to-End Test ---")

    test_question = "What is omi kit ?"
    print(f"Test Question: {test_question}")

    search_results = [
        {
            "question": "What is Omi?", 
            "answer": "Omi is a consumer-facing line of wearable devices focused on fitness and interactive entertainment."
        },
        {
            "question": "What is the Omi Dev Kit?", 
            "answer": "The Omi Dev Kit (ODK) is a package of hardware components, APIs, and software documentation specifically designed for third-party developers to create new applications for the Omi ecosystem."
        },
        {
            "question": "Where can I buy Omi?", 
            "answer": "Omi devices are available for pre-order on our official website starting in Q4 2025."
        }
    ]

    context = "\n".join([f"Question: {r['question']}\nAnswer: {r['answer']}" for r in search_results])
    print(f"\n--- Context Sent to LLM ---\n{context}")

    llm_answer = llm.generate_answer(test_question, context)

    print(f"\n--- LLM Generated Answer ---\n{llm_answer}")

# --- Execution Entry Point ---
if __name__ == "__main__":
    asyncio.run(main())