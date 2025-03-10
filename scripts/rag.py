import os
import spacy
from langchain_community.vectorstores import Neo4jVector
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_neo4j import Neo4jGraph

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class KnowledgeGraphRAG:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        # self.vector_store = self.get_vector_store()
        self.nlp = spacy.load("en_core_web_sm")
        
    
    def get_vector_store(self) -> Neo4jVector:
        print("Creating vector store...")

        embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)

        vector_store = Neo4jVector.from_existing_graph(
            embedding=embedding_model,
            url = self.url,
            username = self.username,
            password = self.password,
            index_name = "topic_index",
            node_label = "Topic",
            text_node_property = ["name", "content"],
            embedding_node_property = "embedding",
        )
        
        print("Vector store created!")
        return vector_store
    
    def extract_topics(self, query: str) -> list:
        """
        Extract topics from a query using spaCy

        :param query: The query to extract topics from

        :return: A list of topics extracted from the query
        """

        doc = self.nlp(query)
        topics = [chunk.text for chunk in doc.noun_chunks if not chunk.root.is_stop and chunk.root.pos_ != 'PRON']
        return topics
    
    def search_query(self, query: str, k=5):
        topics = self.extract_topics(query)
        res = {}

        for topic in topics:
            print(f"Searching content for topic: {topic}")
            self.vector_store.similartiy_search(topic, k)
            res[topic] = self.vector_store.similartiy_search(topic, k)

        return res