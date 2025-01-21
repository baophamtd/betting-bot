import os
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader

load_dotenv()

class LangChainClient:
    def __init__(self, model_name=None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.llm = OpenAI(model_name=model_name) if model_name else OpenAI()
        self.embeddings = OpenAIEmbeddings()

    def process_file_and_query(self, file_path, query, chunk_size=1000, chunk_overlap=0):
        # Load the document
        loader = TextLoader(file_path)
        documents = loader.load()

        # Split the documents into chunks
        text_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        texts = text_splitter.split_documents(documents)

        # Create a vector store
        vectorstore = FAISS.from_documents(texts, self.embeddings)

        # Create a retrieval chain
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever()
        )

        # Run the query
        result = qa_chain.run(query)

        return result

# Example usage:
# client = LangChainClient()
# response = client.process_file_and_query("path/to/your/file.txt", "Your question here?")
# print(response)
