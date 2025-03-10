from langchain_neo4j import Neo4jGraph

def connection(url="bolt://localhost:7687", username="neo4j", password="password123") -> Neo4jGraph:
    """
    Connect to a Neo4j database

    :param url: URL of the Neo4j database
    :param username: Username of the Neo4j database
    :param password: Password of the Neo4j database
    
    :return: A connection to the Neo4j database
    """
    try:
        graph = Neo4jGraph(url, username, password)
        print("Connected to Neo4j!")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return None
    return graph
