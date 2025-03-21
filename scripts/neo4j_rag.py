import os
import spacy
import pickle

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
        self.nlp = spacy.load("en_core_web_sm")
        
    
    def get_vector_store(self, save=True) -> Neo4jVector:
        """Get or create a vector store for the knowledge graph."""

        print("Creating vector store...")

        vector_store = self.load_vector_store()
        if vector_store:
            return vector_store

        vector_store = Neo4jVector.from_existing_graph(
            embedding=self.embedding_model,
            url = self.url,
            username = self.username,
            password = self.password,
            index_name = "topic_index",
            node_label = "Topic",
            text_node_properties = ["name", "content"],
            embedding_node_property = "embedding",
        )
        
        self.vector_store = vector_store
        if save:
            self.save_vector_store()

        print("Vector store created!")
        return vector_store
    
    def save_vector_store(self):
        """Save vector store metadata to a file."""

        if self.vector_store:
            data_to_save = {
                "index_name": "topic_index",
                "node_label": "Topic",
                "text_node_properties": ["name", "content"],
                "embedding_node_property": "embedding",
            }
            with open(self.vector_store_path, "wb") as f:
                pickle.dump(data_to_save, f)
            print("Vector store metadata saved!")

    def load_vector_store(self):
        """Load vector store metadata and reconstruct the object."""

        try:
            with open(self.vector_store_path, "rb") as f:
                data = pickle.load(f)
                print("Loaded vector store metadata from file!")

                return Neo4jVector.from_existing_graph(
                    embedding=self.embedding_model,
                    url=self.url,
                    username=self.username,
                    password=self.password,
                    **data  
                )
        except (FileNotFoundError, EOFError, pickle.UnpicklingError):
            print("No valid vector store found. Creating a new one...")
            return None
    
    def extract_topics(self, query: str) -> list:
        """
        Extract topics from a query using spaCy

        Args:
            query: str, the query to extract topics from

        Returns:
            list: A list of topics extracted from the query
        """

        doc = self.nlp(query)
        topics = [chunk.text for chunk in doc.noun_chunks if not chunk.root.is_stop and chunk.root.pos_ != 'PRON']
        return topics
    
    def search_query(self, query: str) -> dict:
        """
        Search the knowledge graph for content related to a query.

        Args:
            query: str

        Returns:
            dict: A dictionary containing the topics and the content related to the query
        """
        
        topics = self.extract_topics(query)
        res = {}

        for topic in topics:
            print(f"Searching content for topic: {topic}")
            
            search_result = self.vector_store.similarity_search(topic)

            if search_result: 
                text = search_result[0].page_content 
                node_name = text.split("content:")[0].replace("name:", "").strip()
                node_content = text.split("content:")[1].strip() if "content:" in text else ""
                res[topic] = {"name": node_name, "content": node_content}
            else:
                res[topic] = {"name": None, "content": None} 


        return res