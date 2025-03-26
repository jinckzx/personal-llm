import os
import qdrant_client
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.core import Settings
from qdrant_client.http.models import Distance, VectorParams

# Load environment variables
load_dotenv()

class RAGHandler:
    def __init__(self):
        # Set the embedding model
        Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")

        # Load documents
        self.documents = SimpleDirectoryReader("data").load_data()

        # Initialize Qdrant client
        self.q_client = qdrant_client.QdrantClient(
            api_key=os.getenv("QDRANT_API_KEY"),
            url=os.getenv("QDRANT_URL")
        )

        # Collection name
        self.collection_name = os.getenv("QDRANT_COLLECTION")

        # Check if collection exists, otherwise create it
        self._ensure_collection_exists()

        # Set up vector store
        self.vector_store = QdrantVectorStore(
            client=self.q_client, 
            collection_name=self.collection_name
        )

        # Create storage context
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

        # Create index
        self.index = VectorStoreIndex.from_documents(
            self.documents, 
            storage_context=self.storage_context
        )

        # Initialize query engine
        self.query_engine = self.index.as_query_engine()

    def _ensure_collection_exists(self):
        """Check if the Qdrant collection exists, and create it if not."""
        collections = self.q_client.get_collections()
        collection_names = {c.name for c in collections.collections}

        if self.collection_name not in collection_names:
            print(f"Collection '{self.collection_name}' does not exist. Creating a new one...")
            self.q_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)  # Adjust size based on the embedding model
            )

    def get_context(self, prompt: str) -> str:
        """Retrieve context based on the given prompt"""
        response = self.query_engine.query(prompt)
        return str(response)
