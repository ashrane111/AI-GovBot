from main.retriever import Retriever
from main.generator import Generator
from main.mlflow_tracker import MLFlowTracker
from main.config_loader import config_loader
from main.prompt_gen import PromptGen
from main.moderator import Moderator
from datetime import datetime 
import time
import re

class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.generator = Generator()
        self.tracker = MLFlowTracker()
        self.SCORE_THRESHOLD = config_loader.get("retriever_args.score_threshold", 1.2)
        self.prompter = PromptGen()
        self.moderator = Moderator() 

    async def run(self, query_message):
        required_query = query_message[-1]
        query = required_query['content']

        flag, reason = await self.moderator.moderate_content(query)
        if flag == "flagged":
            return {
                "content": "I cannot process this request as it appears to violate content policies.",
                "messages": query_message
            }, []

    
        start_time = time.time()
        retrieved_docs, retrieval_scores = self.retriever.retrieve(query)
        document_id = [str(item).split()[0] if str(item).split() else "" for item in retrieved_docs]
        context = self.__generate_context(retrieved_docs, retrieval_scores)
        prompted_messages = self.prompter.generate_user_prompt(query_message, context)
        retrieval_time = time.time() - start_time
        
        start_time = time.time()
          # Use the filtered context
        answer = await self.generator.generate(prompted_messages)
        answer['messages'] = self.prompter.remove_system_prompt(answer['messages'])
        generation_time = time.time() - start_time

        # New block: Moderate generated response
        flag, reason = await self.moderator.moderate_content(answer['content'])
        if flag == "flagged":
            # Log the flagged content
            self._log_flagged_content(query, answer['content'], reason)
            # Replace with safe response
            answer['content'] = f"I'm unable to provide the requested information as it may violate content policies. Reason: {reason}"


        self.tracker.log_metrics(query, answer, retrieved_docs, retrieval_scores, retrieval_time, generation_time)

        return answer, document_id
    
    def __generate_context(self, retrieved_docs, retrieval_scores):
        filtered_docs = []
        for i, (doc, score) in enumerate(zip(retrieved_docs, retrieval_scores)):
            # Convert score to double (float)
            score_double = float(score)
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
    
    # New method for logging flagged content
    def _log_flagged_content(self, query, response, reason):
        """Log flagged content for review"""
        with open("flagged_content.log", "a") as f:
            f.write(f"--- {datetime.now()} ---\n")
            f.write(f"Query: {query}\n")
            f.write(f"Response: {response}\n")
            f.write(f"Reason: {reason}\n\n")