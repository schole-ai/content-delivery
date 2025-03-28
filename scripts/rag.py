import os
import sys
import numpy as np
import faiss
import time
import logging

logging.basicConfig(level=logging.ERROR)
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from abc import ABC, abstractmethod
from sklearn.metrics.pairwise import cosine_similarity
from utils.helpers import connection
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_LEN = 1536

class Retriever(ABC):
    def __init__(self, url, username, password, node_id, doc_property="documents", doc_embeddings_property="doc_embeddings"):
        self.url = url
        self.username = username
        self.password = password
        self.node_id = node_id
        self.doc_property = doc_property
        self.doc_embeddings_property = doc_embeddings_property
        self.embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        self.driver = connection(url, username, password)
        self.docs = self.get_documents()
        self.embeddings = self.get_embeddings()

    @abstractmethod
    def retrieve_top_k(self, query, k=5):
        pass

    def get_documents(self):
        """
        Get documents from a node in the knowledge graph.

        Returns:
            list: List of documents
        """

        query = f"MATCH (n) WHERE id(n) = {self.node_id} RETURN n.{self.doc_property} AS documents"

        with self.driver.session() as session:
            result = session.run(query).single()
            documents = result["documents"]
        
        return documents
        
    def get_embeddings(self):
        """
        Get embeddings for the documents.

        Returns:
            np.array: embeddings for the documents of shape (nb_docs, EMBEDDING_LEN)
        """

        query = f"MATCH (n) WHERE id(n) = {self.node_id} RETURN n.{self.doc_embeddings_property} AS doc_embeddings"

        with self.driver.session() as session:
            result = session.run(query).single()
            embeddings = result["doc_embeddings"]
            # Reshape embeddings from list[nb_doc * EMBEDDING_LEN] to np.array[nb_doc, EMBEDDING_LEN]
            embeddings = np.array(embeddings).reshape(-1, EMBEDDING_LEN)
        

        return embeddings
    
    
class CosineRetriever(Retriever):
    def __init__(self, url, username, password, node_id, doc_property="documents", doc_embeddings_property="doc_embeddings"):
        super().__init__(url, username, password, node_id, doc_property, doc_embeddings_property)
    
    def retrieve_top_k(self, query, k=1):
        """
        Retrieve the top k documents based on cosine similarity.

        Args:
            query (str): The query to search for.
            k (int): The number of documents to retrieve.

        Returns:
            list: The top k documents.
        """

        start_time = time.time()

        query_embedding = self.embedding_model.embed_query(query)
        query_embedding = np.array(query_embedding).reshape(1, -1)
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_embedding, self.embeddings)
        
        # Get top k indices
        top_k_indices = similarities[0].argsort()[-k:][::-1]
        
        # Get top k documents
        top_k_docs = [self.docs[i] for i in top_k_indices]

        end_time = time.time()

        print(f"Retrieval time: {end_time - start_time:.2f} seconds")
        
        return top_k_indices, top_k_docs
    

class FaissRetriever(Retriever):
    def __init__(self, url, username, password, node_id, doc_property="documents", doc_embeddings_property="doc_embeddings"):
        super().__init__(url, username, password, node_id, doc_property, doc_embeddings_property)
        self.index = faiss.IndexFlatIP(self.embeddings.shape[1])
        self.index.add(self.embeddings)
    
    def retrieve_top_k(self, query, k=1):
        """
        Retrieve the top k documents based on cosine similarity using Faiss.

        Args:
            query (str): The query to search for.
            k (int): The number of documents to retrieve.

        Returns:
            list: The top k documents.
        """

        start_time = time.time()

        query_embedding = self.embedding_model.embed_query(query)
        query_embedding = np.array(query_embedding).reshape(1, -1)
        
        # Search index
        _, top_k_indices = self.index.search(query_embedding, k)
        
        # Get top k documents
        top_k_docs = [self.docs[i] for i in top_k_indices[0]]

        end_time = time.time()

        print(f"Retrieval time: {end_time - start_time:.2f} seconds")
        
        return top_k_indices[0], top_k_docs