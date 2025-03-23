class PromptGen:
    def __init__(self):
        self.system_prompt = {
            "role": "system",
            "content": "You are H.A.R.V.E.Y, which is an acronym for `Holistic AI for Regulatory Verification and Ethical Yield`. "
                       "You work as an AI assistant to help technical teams understand laws surrounding artificial intelligence and its implications. "
                       "A person may ask you questions about AI laws and policies. There will be 2 fields: Context and Query. Context will contain "
                       "the most relevant documents regarding the query and Query will be the question asked by the user. "
                       "You will generate a response based on the context.Look at the `Rank` to decide how relevant the document is."
                       "Sometimes you may not get a context, in that case judge the previous conversation with the user "
                       "and generate a response accordingly. Respond in a brief way. "
        }

    def generate_user_prompt(self, messages, context):
        # Prepend the system prompt to the list of messages
        messages.insert(0, self.system_prompt)
        query = messages[-1]['content']
        user_prompt = {
            "role": "user",
            "content": f"Query: {query}\nContext: {context}"
        }
        messages[-1] = user_prompt
        
        return messages
    def remove_system_prompt(self, messages):
        return messages[1:]

