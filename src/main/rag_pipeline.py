from main.retriever import Retriever
from main.generator import Generator
from main.mlflow_tracker import MLFlowTracker
import time

class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.generator = Generator()
        self.tracker = MLFlowTracker()

    async def run(self, query_message):
        print(query_message)
        required_query = query_message[-1]
        query = required_query['content']
        start_time = time.time()
        retrieved_docs, retrieval_scores = self.retriever.retrieve(query)
        retrieval_time = time.time() - start_time

        start_time = time.time()
        context = " ".join(retrieved_docs)
        answer = await self.generator.generate(context, query_message)
        generation_time = time.time() - start_time

        self.tracker.log_metrics(query, answer, retrieved_docs, retrieval_scores, retrieval_time, generation_time)

        print("\n💬 Generated Answer:", answer['content'])
        return answer