import os
import io
import json
import base64
import sys

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from utils.helpers import *

from unstructured.documents.elements import *
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
    def __init__(self, pdf_path=None, file_obj=None, load_path=None):
        self.pdf_path = pdf_path
        self.file_obj = file_obj
        self.load_path = load_path
        if self.load_path:
            self.formated_chunks, self.chunks_img_b64 = self.load_chunks(self.load_path)
        else:
            self.chunks = self.partition()
            self.formated_chunks = [self.format_chunk(chunk) for chunk in self.chunks]
            self.chunks_img = [self.crop_chunk_on_page(chunk) for chunk in self.chunks]
            self.chunks_img_b64 = [self.pil_image_to_base64(chunk) for chunk in self.chunks_img]

    def partition(self, max_characters=1500, combine_text_under_n_chars=500, new_after_n_chars=1000):
        """Partition the PDF into chunks."""
        if self.file_obj:
            chunks = partition_pdf(
                file=self.file_obj,
                infer_table_structure=True,
                strategy="hi_res", 
                extract_image_block_types=["Image"],
                extract_image_block_to_payload=True,
                chunking_strategy="by_title",
                max_characters=max_characters,
                combine_text_under_n_chars=combine_text_under_n_chars,
                new_after_n_chars=new_after_n_chars,
            )
        elif self.pdf_path:
            chunks = partition_pdf(
                filename=self.pdf_path,
                infer_table_structure=True,
                strategy="hi_res", 
                extract_image_block_types=["Image"],
                extract_image_block_to_payload=True,
                chunking_strategy="by_title",
                max_characters=max_characters,
                combine_text_under_n_chars=combine_text_under_n_chars,
                new_after_n_chars=new_after_n_chars,
            )
        else:
            raise ValueError("Either pdf_path or file_obj must be provided.")

        return chunks
    
    def get_image_base64(self, image_element: Image) -> str:
        """Get base64 code from image element."""
        return image_element.metadata.image_base64
    
    def pil_image_to_base64(self, image: PILImage) -> str:
        """Convert PIL image to base64 string."""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
    
    def format_chunk(self, chunk):
        """Format chunk."""
        texts = []
        images = []
 
        for element in chunk.metadata.orig_elements:
            # skip footer and header elements
            if isinstance(element, (Header, Footer)): continue
            # skip uncategorized text elements
            if element.to_dict().get("type") == "UncategorizedText": continue
            if isinstance(element, Image):
                b64_code = self.get_image_base64(element)
                if b64_code:
                    images.append(Document(page_content=b64_code, metadata={"type": "image"}))
                continue
            if isinstance(element, Table):
                texts.append(Document(page_content=element.metadata.text_as_html, metadata={"type": "text"}))
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
        pages = convert_pdf_to_images(pdf_path=self.pdf_path, file_obj=self.file_obj)
        page_image = pages[current_page_number - 1]
        img = page_image.copy()
        draw = ImageDraw.Draw(img)


        for el in chunk.metadata.orig_elements:
            if el.to_dict().get("type") == "UncategorizedText": continue
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
        pages = convert_pdf_to_images(pdf_path=self.pdf_path, file_obj=self.file_obj)
        page_image = pages[current_page_number - 1]
        img = page_image.copy()

        x0, y0, x1, y1 = [], [], [], []

        for el in chunk.metadata.orig_elements:
            if el.to_dict().get("type") == "UncategorizedText": continue
            el_page_number = el.metadata.page_number
            if el_page_number != current_page_number:
                # Crop and store the previous page image
                if x0 and y0 and x1 and y1:
                    cropped_img = img.crop((min(x0), min(y0), max(x1), max(y1)))
                    imgs.append(cropped_img)

                # Reset for the new page
                current_page_number = el_page_number
                page_image = pages[current_page_number - 1]
                img = page_image.copy()
                x0, y0, x1, y1 = [], [], [], []

            coords = el.metadata.coordinates.points
            box = get_scaled_coords(coords, scale_x, scale_y) 
            x0.append(min(p[0] for p in box))
            y0.append(min(p[1] for p in box))
            x1.append(max(p[0] for p in box))
            y1.append(max(p[1] for p in box))

        if x0 and y0 and x1 and y1:
            cropped_img = img.crop((min(x0), min(y0), max(x1), max(y1)))
            imgs.append(cropped_img)

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

    def save_chunks(self, path):
        """
        Save formatted chunks and chunk images (as base64) to a JSON file.
        """
        data = []
        for chunk, img_b64 in zip(self.formated_chunks, self.chunks_img_b64):
            chunk_data = []
            for doc in chunk:
                chunk_data.append({
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                })
            data.append({
                "formated_chunk": chunk_data,
                "chunk_img_b64": img_b64
            })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_chunks(self, path):
        """
        Load formatted chunks and chunk images (as base64) from a JSON file.
        Returns: (formated_chunks, chunks_img, chunks_img_b64)
        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        formated_chunks = []
        chunks_img_b64 = []
        chunks_img = []
        for entry in data:
            chunk_docs = []
            for doc in entry["formated_chunk"]:
                chunk_docs.append(Document(page_content=doc["page_content"], metadata=doc["metadata"]))
            formated_chunks.append(chunk_docs)
            img_b64 = entry["chunk_img_b64"]
            chunks_img_b64.append(img_b64)

        return formated_chunks, chunks_img_b64

