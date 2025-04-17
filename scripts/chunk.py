import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from utils.helpers import *

from unstructured.documents.elements import Footer, Header, Image
from PIL import Image as PILImage, ImageDraw


from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents import Document

from chunking_evaluation.chunking import ClusterSemanticChunker, LLMSemanticChunker

from semantic_chunkers import StatisticalChunker
from semantic_router.encoders import OpenAIEncoder

from unstructured.partition.pdf import partition_pdf


from dotenv import load_dotenv


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEPARATORS = ["\n\n", "\n", ".", "?", "!", " ", ""]

class TextChunker:
    """A class which implements many methods for create bite-sized blocks of text."""
    def __init__(self, text, output_document=True):
        self.text = text
        self.output_document = output_document
        self.embedding_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        self.encoder_model = OpenAIEncoder(name="text-embedding-3-small")

    def recursive_chunk(self, chunk_size=500, chunk_overlap=0, by_tokens=False):
        """Chunk text recursively."""
        if by_tokens:
            splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(model_name="gpt-4", 
                                                                            chunk_size=chunk_size,
                                                                            chunk_overlap=chunk_overlap,
                                                                            separators=SEPARATORS)
        else:
            splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, 
                                                      chunk_overlap=chunk_overlap,
                                                      separators=SEPARATORS)
            
        chunks = splitter.split_text(self.text)
        return self.output_format(chunks)

    def semantic_chunk(self):
        """Chunk text based on semantic similarity."""
        splitter = SemanticChunker(self.embedding_model)
        chunks = splitter.split_text(self.text)
        return self.output_format(chunks)
    
    def cluster_chunk(self, max_chunk_size=500):
        """Chunk text based on clustering."""
        splitter = ClusterSemanticChunker(
            embedding_function=self.embedding_model.embed_documents,
            max_chunk_size=max_chunk_size
        )
        chunks = splitter.split_text(self.text)
        return self.output_format(chunks)
    
    def llm_chunk(self):
        """Chunk text based on LLMs."""
        splitter = LLMSemanticChunker(
            organisation="openai",
            model_name="gpt-4o",
            api_key=OPENAI_API_KEY
        )
        chunks = splitter.split_text(self.text)
        return self.output_format(chunks)

    def statistical_chunk(self):
        """Chunk text based on statistical methods."""
        splitter = StatisticalChunker(encoder=self.encoder_model)
        chunks = splitter(docs=[self.text])[0]
        chunk_texts = [' '.join(chunk.splits) for chunk in chunks]
        return self.output_format(chunk_texts)
    
    def output_format(self, chunks):
        """Format the output."""
        if self.output_document:
            return [[Document(page_content=chunk, metadata={"type": "text"})] for chunk in chunks]
        return chunks
    

class PDFChunker:
    """A class which extracts content from PDFs and chunks it."""
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.chunks = self.partition()
        self.formated_chunks = [self.format_chunk(chunk) for chunk in self.chunks]
        self.chunks_img = [self.crop_chunk_on_page(chunk) for chunk in self.chunks]

    def partition(self):
        chunks = partition_pdf(
            filename=self.pdf_path,
            infer_table_structure=True,
            strategy="hi_res", 
            extract_image_block_types=["Image"],
            extract_image_block_to_payload=True,
            chunking_strategy="by_title", # or "basic"
            max_characters=6000,
            combine_text_under_n_chars=1500,
            new_after_n_chars=4000,
        )

        return chunks
    
    def get_image_base64(self, image_element: Image) -> str:
        """Get base64 code from image element."""
        return image_element.metadata.image_base64
    
    def format_chunk(self, chunk):
        """Format chunk."""
        texts = []
        images = []
 
        for element in chunk.metadata.orig_elements:
            # skip footer and header elements
            if isinstance(element, (Header, Footer)): continue
            if isinstance(element, Image):
                b64_code = self.get_image_base64(element)
                if b64_code:
                    images.append(Document(page_content=b64_code, metadata={"type": "image"}))
                continue
            if hasattr(element, "text"):
                texts.append(Document(page_content=element.text.strip(), metadata={"type": "text"}))
                 
        return texts + images
    
    def highlight_chunk_on_page(self, chunk, scale_x=1.0, scale_y=1.0, combined=True):
        """
        Draw red boxes on the pdf pages around all elements in the chunk.
        
        Args:
            chunk (Document): The chunk to highlight.
            scale_x (float): Scale factor for x-coordinates.
            scale_y (float): Scale factor for y-coordinates.
            combined (bool): If True, combine all pdf pages into one image.
            
        
        Returns:
            PILImage: The image with highlighted elements or a list of images if combined is False.
        """

        imgs = []
        current_page_number = chunk.metadata.page_number
        pages = convert_pdf_to_images(self.pdf_path)
        page_image = pages[current_page_number - 1]
        img = page_image.copy()
        draw = ImageDraw.Draw(img)


        for el in chunk.metadata.orig_elements:
            if el.metadata.page_number != current_page_number:
                imgs.append(img)
                current_page_number = el.metadata.page_number
                page_image = pages[current_page_number - 1]
                img = page_image.copy()
                draw = ImageDraw.Draw(img)
                
            coords = el.metadata.coordinates.points
            box = get_scaled_coords(coords, scale_x, scale_y)  
            x0 = min(p[0] for p in box)
            y0 = min(p[1] for p in box)
            x1 = max(p[0] for p in box)
            y1 = max(p[1] for p in box)

            draw.rectangle([x0, y0, x1, y1], outline="red", width=3)
        
        imgs.append(img)

        if combined:
            combined_img = self.combine_images_vertically(imgs, padding=-250, bg_color=(255, 255, 255))
            return combined_img
        
        return imgs
    
    def crop_chunk_on_page(self, chunk, scale_x=1.0, scale_y=1.0, combined=True):
        """
        Crop the chunk from the page.
        
        Args:
            chunk (Document): The chunk to crop.
            scale_x (float): Scale factor for x-coordinates.
            scale_y (float): Scale factor for y-coordinates.
            combined (bool): If True, combine all pdf pages into one image.
        
        Returns:
            PILImage: The cropped image of the chunk or a list of cropped images if combined is False.
        """

        imgs = []
        current_page_number = chunk.metadata.page_number
        pages = convert_pdf_to_images(self.pdf_path)
        page_image = pages[current_page_number - 1]
        img = page_image.copy()

        x0, y0, x1, y1 = [], [], [], []

        for el in chunk.metadata.orig_elements:         
            coords = el.metadata.coordinates.points
            box = get_scaled_coords(coords, scale_x, scale_y)  

            x0.append(min(p[0] for p in box))
            y0.append(min(p[1] for p in box))
            x1.append(max(p[0] for p in box))
            y1.append(max(p[1] for p in box))

            if el.metadata.page_number != current_page_number:
                img = img.crop((min(x0), min(y0), max(x1), max(y1)))

                x0, y0, x1, y1 = [], [], [], []

                imgs.append(img)
                current_page_number = el.metadata.page_number
                page_image = pages[current_page_number - 1]
                img = page_image.copy()

        img = img.crop((min(x0), min(y0), max(x1), max(y1)))
        imgs.append(img)

        if combined:
            combined_img = self.combine_images_vertically(imgs, padding=0, bg_color=(255, 255, 255))
            return combined_img
        return imgs
    
    def combine_images_vertically(self, images, padding=0, bg_color=(255, 255, 255)):
        """
        Combine a list of images vertically into one single image.
        Optionally adds padding between them.

        Args:
            images (list): List of PIL Image objects to combine.
            padding (int): Padding between images.
            bg_color (tuple): Background color for the combined image.

        Returns:
            PILImage: Combined image.
        """
        widths = [img.width for img in images]
        heights = [img.height for img in images]

        total_width = max(widths)
        total_height = sum(heights) + padding * (len(images) - 1)

        combined = PILImage.new('RGB', (total_width, total_height), color=bg_color)

        y_offset = 0
        for img in images:
            combined.paste(img, (0, y_offset))
            y_offset += img.height + padding

        return combined

