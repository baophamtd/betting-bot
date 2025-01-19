from contextlib import ExitStack
import os
from openai import OpenAI
import re

class OpenAIClient:
    def __init__(self):
        self.client = OpenAI()
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

    def create_assistant(self, instructions, assistant_name, model_name="gpt-4o-mini"):
        """
        Create an assistant using the OpenAI client library.
        
        :param model_name: The model to be used (e.g., "gpt-4o")
        :param instructions: Instructions for the assistant
        :param assistant_name: The name of the assistant
        :return: The created assistant object
        """
        # Check if an assistant with the given name already exists
        existing_assistants = self.client.beta.assistants.list()
        for existing_assistant in existing_assistants:
            if existing_assistant.name == assistant_name:
                print(f"Assistant with name '{assistant_name}' already exists.")
                return existing_assistant

        assistant = self.client.beta.assistants.create(
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
    
    def create_vector_store_for_assistant_with_file_paths(self, assistant_id, vector_store_name, file_paths):
        """
        Create a vector store for the given assistant.
        
        :param assistant_id: The ID of the assistant
        :param vector_store_name: The name of the vector store
        :return: The created vector store object
        """
        vector_store = self.client.beta.vector_stores.create(name=vector_store_name)  
        
        # Using ExitStack to manage multiple context managers and ensure they are properly closed.
        with ExitStack() as stack:
            # Open each file in binary read mode and add the file stream to the list
            file_streams = [stack.enter_context(open(path, "rb")) for path in file_paths]

            # Use the upload and poll helper method to upload the files, add them to the vector store,
            # and poll the status of the file batch for completion.
            file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id, files=file_streams
            )

            # Print the vector store information
            print(vector_store.name)
            print(vector_store.id)
            
            # Print the status and the file counts of the batch to see the results
            print(file_batch.status)
            print(file_batch.file_counts)
            print(f"File upload status {file_batch.status}")                                                                     

        # Update The Assistant With A Vector Store
        assistant = self.client.beta.assistants.update(
          assistant_id=assistant_id,
          tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )
        print("Assistant Updated with vector store!")
        return assistant

    def query_assistant(self, assistant_id, query):
        """
        Query the assistant with a given input.
        
        :param assistant_id: The ID of the assistant
        :param query: The input query for the assistant
        :return: The assistant's response
        """
        thread = self.client.beta.threads.create()
        message = self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query,
        )
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant_id
        )
        messages = list(self.client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
        response = messages[0].content[0].text.value
        return response
    
    def delete_all_vector_stores(self):
        """
        Delete all vector stores.
        """
        # Get a list of our vector stores up to the limit
        # The default page limit is 100, but we can specify a different limit
        # Use "after" to go through more than 100 vector stores
        vector_stores = self.client.beta.vector_stores.list()

        # Convert the SyncCursorPage to a list to get the number of 
        # vector stores in the current page
        vector_store_list = list(vector_stores.data)

        # Show the number of vector stores in the current page
        print("Vector Stores: " + str(len(vector_store_list)))
        
        # Now let's delete the vector stores in our list of retrieved vector stores
        for vector_store in vector_store_list:
            try:
                # Delete the vector store
                self.client.beta.vector_stores.delete(vector_store_id=vector_store.id)
                print(f"Deleted vector store with Name: {vector_store.name}" 
                        + f"\nDeleted vector store with ID: {vector_store.id}\n\n")
            except Exception as e:
                print(f"An error occurred while deleting the vector store: {e}")