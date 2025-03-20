from src.main.retriever import Retriever
from src.main.generator import Generator
from src.main.mlflow_tracker import MLFlowTracker

class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.generator = Generator()
        self.tracker = MLFlowTracker()

    def run(self, query):
        retrieved_docs, retrieval_scores = self.retriever.retrieve(query)
        print("\n🔍 Retrieved Documents:", retrieved_docs)
        print("🔢 Retrieval Scores:", retrieval_scores)

        context = " ".join(retrieved_docs)
        answer = self.generator.generate(context, query)

        answer['retrieved_documents'] = retrieved_docs
        answer['retrieval_scores'] = retrieval_scores

        self.tracker.log_metrics(query, answer, retrieved_docs, retrieval_scores)

        print("\n💬 Generated Answer:", answer['content'])
        return answer

if __name__ == "__main__":
    pipeline = RAGPipeline()
    test_query = "She seemed to feel threatened by us and it was difficult to calm her down."
    pipeline.run(test_query)