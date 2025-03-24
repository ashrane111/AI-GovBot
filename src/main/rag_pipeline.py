from main.retriever import Retriever
from main.generator import Generator
from main.mlflow_tracker import MLFlowTracker
from main.config_loader import config_loader
from main.prompt_gen import PromptGen
import time
import re

class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.generator = Generator()
        self.tracker = MLFlowTracker()
        self.SCORE_THRESHOLD = config_loader.get("retriever_args.score_threshold", 1.2)
        self.prompter = PromptGen()

    async def run(self, query_message):
        print(query_message)
        required_query = query_message[-1]
        query = required_query['content']
        start_time = time.time()
        retrieved_docs, retrieval_scores = self.retriever.retrieve(query)
        document_id = [str(item).split()[0] if str(item).split() else "" for item in retrieved_docs]
        context = self.__generate_context(retrieved_docs, retrieval_scores)
        print("\n🔍 Retrieved Context:\n", context)
        prompted_messages = self.prompter.generate_user_prompt(query_message, context)
        retrieval_time = time.time() - start_time
        
        start_time = time.time()
          # Use the filtered context
        answer = await self.generator.generate(prompted_messages)
        answer['messages'] = self.prompter.remove_system_prompt(answer['messages'])
        generation_time = time.time() - start_time

        self.tracker.log_metrics(query, answer, retrieved_docs, retrieval_scores, retrieval_time, generation_time)

        return answer, document_id
    
    def __generate_context(self, retrieved_docs, retrieval_scores):
        print("\n🔍 Retrieved Documents:")
        filtered_docs = []
        for i, (doc, score) in enumerate(zip(retrieved_docs, retrieval_scores)):
            # Convert score to double (float)
            score_double = float(score)
            print(f"Document {i+1} ({score_double:.4f}): {doc[:100]}...")
            if score_double < self.SCORE_THRESHOLD:
                context_doc = f"Rank {i+1}: " + self.__get_context_doc(doc)
                filtered_docs.append(context_doc)
            else:
                print(f"  [FILTERED OUT - score above threshold {self.SCORE_THRESHOLD}]")
        return "\n".join(filtered_docs)

    def __get_context_doc(self, doc):
        # Extract the relevant context from the document
        # Strip unnecessary lines and extra spaces
        doc = doc.strip()
        doc = re.sub(r'\n\s*\n', '\n', doc)  # Replace multiple newlines with a single newline
        lines = doc.split('\n')
        filtered_lines = [line.strip() for line in lines if line.strip()]  # Remove empty lines and strip each line
        return "\n".join(filtered_lines)