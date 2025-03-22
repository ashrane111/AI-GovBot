from main.retriever import Retriever
from main.generator import Generator
from main.mlflow_tracker import MLFlowTracker
import time

class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.generator = Generator()
        self.tracker = MLFlowTracker()

    def run(self, query):
        start_time = time.time()
        retrieved_docs, retrieval_scores = self.retriever.retrieve(query)
        retrieval_time = time.time() - start_time

        start_time = time.time()
        context = " ".join(retrieved_docs)
        answer = self.generator.generate(context, query)
        generation_time = time.time() - start_time

        self.tracker.log_metrics(query, answer, retrieved_docs, retrieval_scores, retrieval_time, generation_time)

        print("\n💬 Generated Answer:", answer['content'])
        return answer