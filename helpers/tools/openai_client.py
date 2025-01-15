import openai
import os
from openai import AssistantEventHandler  # Used for handling events related to OpenAI assistants


class OpenAIClient:

    def create_assistant(self, instructions, assistant_name, model_name="gpt-4o"):
        """
        Create an assistant using the OpenAI client library.
        
        :param model_name: The model to be used (e.g., "gpt-4o")
        :param instructions: Instructions for the assistant
        :param assistant_name: The name of the assistant
        :return: The created assistant object
        """
        # Check if an assistant with the given name already exists
        existing_assistants = openai.Assistant.list()
        for existing_assistant in existing_assistants:
            if existing_assistant.name == assistant_name:
                print(f"Assistant with name '{assistant_name}' already exists.")
                return existing_assistant

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
