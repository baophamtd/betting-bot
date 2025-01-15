import openai
import os

class OpenAIClient:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        openai.api_key = self.api_key

    def create_assistant(self, model_name, instructions, assistant_name):
        """
        Create an assistant using the OpenAI client library.
        
        :param model_name: The model to be used (e.g., "gpt-4o")
        :param instructions: Instructions for the assistant
        :param assistant_name: The name of the assistant
        :return: The created assistant object
        """
        assistant = openai.Assistant.create(
            model=model_name,
            instructions=instructions,
            name=assistant_name,
            tools=[{"type": "file_search"}],
            metadata={
                "can_be_used_for_file_search": "True",
                "can_hold_vector_store": "True",
            },
            temperature=1,
            top_p=1,
        )
        return assistant
