import os

from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class KnowledgeGraphRAG:
    def __init__(self, url, username, password, vector_store_path="data/vector_store.pkl"):
        self.url = url
        self.username = username
        self.password = password
        self.vector_store_path = vector_store_path
        self.embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        self.vector_store = self.get_vector_store()
            
    def get_vector_store(self) -> Neo4jVector:
        """Get or create a vector store for the knowledge graph."""

        print("Creating vector store...")

        vector_store = Neo4jVector.from_existing_graph(
            embedding = self.embedding_model,
            url = self.url,
            username = self.username,
            password = self.password,
            index_name = "topic_index",
            node_label = "Topic",
            text_node_properties = ["name", "content"],
            embedding_node_property = "embedding",
        )
        
        self.vector_store = vector_store

        print("Vector store created!")
        return vector_store
    
    def search_query(self, query) -> list:
        """
        Search the knowledge graph for content related to a query.

        Args:
            query (str): The query to search for
            k (int): The number of top results to return

        Returns:
            list: A list of node IDs related to the query
        """
        res = self.vector_store.similarity_search(query, k=1)

        text = res[0].page_content
        content = text.split("content:")[1].strip() if "content:" in text else ""

        return content