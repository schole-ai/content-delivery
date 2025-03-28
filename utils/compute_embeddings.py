import json
import os
import sys
import itertools
import logging
import time

logging.basicConfig(level=logging.ERROR)
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from tqdm import tqdm
from helpers import connection
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_LEN = 1536


def get_nodes(doc_property="documents", url="bolt://localhost:7687", username="neo4j", password="password123"): 
    """
    Get the nodes and their documents from the knowledge graph.

    Args:
        doc_property (str): The property name of the documents.
        url (str): The URL of the Neo4j database.
        username (str): The username of the Neo4j database.
        password (str): The password of the Neo4j database.

    Returns:
        list: List of nodes with their documents.
    """

    driver = connection(url, username, password)

    with driver.session() as session:
        query = f"MATCH (n) WHERE n.{doc_property} IS NOT NULL RETURN id(n) AS id, n.{doc_property} AS documents, n.name AS name"
        results = session.run(query)
        return [{"id": record["id"], "documents": record["documents"], "name": record["name"]} for record in results]


def create_embeddings(nodes):
    """
    Create embeddings for the documents of the nodes.

    Args:
        nodes (list): List of nodes with their documents.

    Returns:
        list: List of embeddings with the node id.
    """

    embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    embeddings = []

    for node in tqdm(nodes, desc="Creating embeddings"):
        embedding = embedding_model.embed_documents(node["documents"])
        embeddings.append({"id": node["id"], "embedding": embedding})
    
    return embeddings

def store_embeddings_locally(embeddings, folder="data", filename="embeddings.json"):
    """
    Store the embeddings locally.

    Args:
        embeddings (list): List of embeddings with the node id.
        folder (str): The folder to store the embeddings.
        filename (str): The filename to store the embeddings.
    """

    filepath = os.path.join(folder, filename)

    if not os.path.exists(folder):
        os.makedirs(folder)

    with open(filepath, "w") as f:
        json.dump(embeddings, f, indent=4)

    print(f"Embeddings saved to {filepath}.")


def store_embeddings_neo4j(embeddings, url="bolt://localhost:7687", username="neo4j", password="password123"):
    """
    Store the embeddings in Neo4j.

    Args:
        embeddings (list): List of embeddings with the node id.
        url (str): The URL of the Neo4j database.
        username (str): The username of the Neo4j database.
        password (str): The password of the Neo4j database.
    """

    driver = connection(url, username, password)

    with driver.session() as session:
        batch_size = 100  
        for i in tqdm(range(0, len(embeddings), batch_size), desc="Storing embeddings"):
            batch = embeddings[i:i + batch_size]
            for emb in batch:
                emb_flat = list(itertools.chain(*emb["embedding"]))
                query = """
                    MATCH (n) WHERE id(n) = $node_id
                    SET n.doc_embeddings = $emb_flat
                """
                session.run(query, {"node_id": emb["id"], "emb_flat": emb_flat})

            time.sleep(1) 


    print("Embeddings stored in Neo4j!")
    


if __name__ == "__main__":
    if os.path.exists("data/embeddings.json"):
        print("Embeddings already created!")
        embeddings = json.load(open("data/embeddings.json"))
    else:
        nodes = get_nodes()
        embeddings = create_embeddings(nodes)
        store_embeddings_locally(embeddings)

    store_embeddings_neo4j(embeddings)