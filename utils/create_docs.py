import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from helpers import connection
from scripts.chunk import TextChunker
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

##############################################
# Create synthetic documents from Neo4j data #
# by chunking the content into smaller parts #
##############################################

def get_content(url="bolt://localhost:7687", username="neo4j", password="password123"):
    """
    Get content from Neo4j nodes.

    Args:
        url: str, URL of the Neo4j database.
        username: str, username for the Neo4j database.
        password: str, password for the Neo4j database.

    Returns:
        list: List of dictionaries containing the node ID, content and name.
    """

    driver = connection(url, username, password)

    with driver.session() as session:
        query = "MATCH (n) WHERE n.content IS NOT NULL RETURN id(n) AS id, n.content AS content, n.name AS name"
        results = session.run(query)
        return [{"id": record["id"], "content": record["content"], "name": record["name"]} for record in results]


def create_docs():
    tc = TextChunker()
    docs = get_content()
    for doc in docs:
        doc["chunks"] = tc.recursive_chunk(doc["content"], chunk_size=1024, by_tokens=True)
    
    return docs

def save_to_file(docs, folder="data", filename="docs.json"):
    filepath = os.path.join(folder, filename)

    if not os.path.exists(folder):
        os.makedirs(folder)

    with open(filepath, "w") as f:
        json.dump(docs, f, indent=4)

    print(f"Docs saved to {filepath}.")


def update_nodes(filepath="data/docs.json", url="bolt://localhost:7687", username="neo4j", password="password123"):

    driver = connection(url, username, password)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    with driver.session() as session:
        for node in data:
            node_id = node["id"]
            chunks = node["chunks"]

            update_query = """
            MATCH (n) WHERE id(n) = $id
            SET n.documents = $documents
            """
            session.run(update_query, id=node_id, documents=chunks)

    print("Neo4j graph updated with document chunks.")

    driver.close()


if __name__ == "__main__":
    docs = create_docs()
    print("Docs created.")
    save_to_file(docs)
    update_nodes()