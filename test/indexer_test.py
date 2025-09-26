import asyncio
import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from core.indexer import FAQIndexer

async def run_tests():
    """Main asynchronous function to run all tests."""
    print("--- Initializing FAQIndexer ---")
    
    indexer = FAQIndexer()
    
    # Check the status of the index
    stats = indexer.get_stats()
    print("Indexer Stats:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")
        
    print("\n--- Running Search Tests ---")
    
    # A list of queries to test the search functionality
    test_queries: List[str] = [
        "What is omi?",
        "Tell me about the omi device",
        "Where can I get one?",
        "What are its features?",
        "What languages does it support?",
        "What is the capital of France?",
        "what is the difference between Omi and Omi Dev Kit ?"
    ]
    
    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        
        # Perform the search
        results: List[Dict] = await indexer.search(query)
        
        if not results:
            print("  - No relevant results found.")
            continue
            
        # Print the top results with their scores
        for i, result in enumerate(results, 1):
            print(f"  - Result {i}:")
            print(f"    - Matched Q: {result['question']}")
            print(f"    - Score: {result['score']:.2f}")
            print(f"    - Confidence: {result['confidence']}")
            print(f"    - Answer: {result['answer'][:50]}...")
            
    print("\n--- Testing get_best_answer ---")
    
    # Test getting the single best answer
    best_query = "What is omi?"
    best_answer, score = await indexer.get_best_answer(best_query)
    
    if best_answer:
        print(f"Query: '{best_query}'")
        print(f"Best Answer Found (Score: {score:.2f}):")
        print(f"  {best_answer}")
    else:
        print(f"Query: '{best_query}' - No single best answer found.")

if __name__ == "__main__":
    asyncio.run(run_tests())

