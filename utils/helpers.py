import os
import re
import base64
from neo4j import GraphDatabase
from IPython.display import display, HTML, Image
from PyPDF2 import PdfReader
from pdf2image import convert_from_path, convert_from_bytes

def connection(url="bolt://localhost:7687", username="neo4j", password="password123") -> GraphDatabase:
    """
    Connect to a Neo4j database

    Args:
        url (str): URL of the Neo4j database
        username (str): Username for authentication
        password (str): Password for authentication
    
    Returns:
        GraphDatabase: A Neo4j driver instance
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

    Args:
        chunks (list): List of text chunks to display
        num_chunks (int, optional): Number of chunks to display. If None, display all chunks.
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


def load_pdf(file_path):
    """
    Load a PDF file and extract text from it

    Args:
        file_path (str): Path to the PDF file
    
    Returns:
        str: Extracted text from the PDF
    """
    
    assert file_path.endswith(".pdf"), "File must be a PDF"
    assert os.path.exists(file_path), "File does not exist"

    with open(file_path, "rb") as file:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    
    return text

def load_txt(file_path):
    """
    Load a text file

    Args:
        file_path (str): Path to the text file
    
    Returns:
        str: Content of the text file
    """
    
    assert file_path.endswith(".txt"), "File must be a TXT"
    assert os.path.exists(file_path), "File does not exist"

    with open(file_path, "r") as file:
        text = file.read()
    
    return text


def clean_pdf_text(text):
    """
    Clean the extracted text from a PDF file

    Args:
        text (str): Extracted text
    
    Returns:
        str: Cleaned text
    """
    # Remove non-printable ASCII characters (0x00 - 0x1F and 0x7F)
    return re.sub(r'[\x00-\x1F\x7F]', '', text)


def display_base64_image(base64_code):
    """
    Display a base64 encoded image in a Jupyter notebook

    Args:
        base64_code (str): Base64 encoded image string
    """
    # Decode the base64 string
    image_data = base64.b64decode(base64_code)
    
    # Display the image
    display(Image(data=image_data))


def convert_pdf_to_images(pdf_path=None, file_obj=None, dpi=200):
    """
    Convert each page of a PDF file to an image

    Args:
        pdf_path (str): Path to the PDF file
        dpi (int): Resolution of the images

    Returns:
        list: List of images converted from the PDF 
    """
    # Convert PDF to images
    if pdf_path:
        return convert_from_path(pdf_path, dpi=dpi)
    elif file_obj:
        file_obj.seek(0)
        return convert_from_bytes(file_obj.read(), dpi=dpi)
    else:
        raise ValueError("Either pdf_path or file_obj must be provided")


def get_scaled_coords(coords, scale_x=1.0, scale_y=1.0):
    """
    Scale coordinates based on the image size.
    
    Args:
        coords (list): List of coordinates to scale.
        scale_x (float): Scale factor for x-coordinates.
        scale_y (float): Scale factor for y-coordinates.

    Returns:
        list: List of scaled coordinates.
    """
    return [(int(x * scale_x), int(y * scale_y)) for x, y in coords]