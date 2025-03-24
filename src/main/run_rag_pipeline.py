import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main.rag_pipeline import RAGPipeline

async def main():
    pipeline = RAGPipeline()
    query = input("Enter your query: ")
    query_dict = [{"role": "user", "content": query}]
    messages = await pipeline.run(query_dict)
    print(messages)

if __name__ == "__main__":
    asyncio.run(main())