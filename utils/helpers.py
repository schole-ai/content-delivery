from neo4j import GraphDatabase
from IPython.display import display, HTML

def connection(url="bolt://localhost:7687", username="neo4j", password="password123") -> GraphDatabase:
    """
    Connect to a Neo4j database

    :param url: URL of the Neo4j database
    :param username: Username of the Neo4j database
    :param password: Password of the Neo4j database
    
    :return: A Neo4j driver instance
    """
    try:
        driver = GraphDatabase.driver(url, auth=(username, password))
        print("Connected to Neo4j!")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return None
    return driver


def display_chunks(chunks, num_chunks=None):
    """
    Display a list of text chunks in a table format

    :param chunks: A list of text chunks
    :param num_chunks: The number of chunks to display
    """

    html_content = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid black;
            padding: 8px;
            text-align: center;
        }
        td {
            text-align: justify;
        }
    </style>
    <table>
        <tr><th>Index</th><th>Chunk</th></tr>
    """
    
    if num_chunks is None: num_chunks = len(chunks)
    
    # Add each chunk to the HTML table
    for idx, chunk in enumerate(chunks[:num_chunks]):
        html_content += f"<tr><td>{idx}</td><td>{chunk}</td></tr>"
    
    html_content += "</table>"
    
    # Display the HTML content
    display(HTML(html_content))


