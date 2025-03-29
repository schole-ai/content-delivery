import os
import requests
import sys

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from openai import OpenAI
from utils.prompts import create_prompt
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BLOOM_TAXONOMY = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze", 5: "Evaluate", 6: "Create"}
BLOOM_BERT_MAP = {"Remember": 1, "Understand": 2, "Apply": 3, "Analyse": 4, "Evaluate": 5, "Create": 6}

# URL for BloomBERT API (https://github.com/RyanLauQF/BloomBERT?tab=readme-ov-file)
BLOOM_BERT_URL = "https://bloom-bert-api-dmkyqqzsta-as.a.run.app/predict"


class BloomQuestionGenerator:
    def __init__(self, model="gpt-4"):
        self.model = model
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    

    def generate_question(self, text, question_type="MCQ", level=1, prompt_type="basic"):
        """
        Generate a question from text based on Bloom's Taxonomy.

        Args:
            text (str): Text to generate questions from.
            question_type (str): Type of question to generate. Options are "MCQ" or "SAQ".
            level (int): Bloom's Taxonomy level to generate questions from.
            prompt_type (str): Type of prompt to use. Options are "basic" or "description".
        
        Returns:
            str: Generated question.
        """

        assert question_type in ["MCQ", "SAQ"], "Invalid question type. Options are 'MCQ' or 'SAQ."
        assert level in range(1, 7), "Invalid Bloom's Taxonomy level. Level should be between 1 and 6."

        prompt = create_prompt(text, question_type, BLOOM_TAXONOMY[level], prompt_type)
       
        messages = [{"role": "system", "content": prompt[0]},
                    {"role": "user", "content": prompt[1]}]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.5
        )

        question = response.choices[0].message.content

        return question
    

    def evaluate_question(self, question, level):
        """
        Evaluate the Bloom's Taxonomy level of a generated question using BloomBERT.

        Args:
            question (str): Question to evaluate.
            level (int): Bloom's Taxonomy level to compare with (ground truth).

        Returns:
            bool: True if the question is at the correct Bloom's Taxonomy level, False otherwise.
        """

        assert level in range(1, 7), "Invalid Bloom's Taxonomy level. Level should be between 1 and 6."

        question_data = {"text": question}

        try:

            response = requests.post(BLOOM_BERT_URL, json=question_data)

            response.raise_for_status()

            response_dict = response.json()
            # print(response_dict)

            predicted_level = BLOOM_BERT_MAP.get(response_dict.get("blooms_level"))

            return predicted_level, predicted_level == level

        except Exception as e:
            print(f"Error: {e}")
            return False


    def check_answer(self, question, answer):
        """
        Check if the answer is correct for a given question.

        Args:
            question (str): Question to check the answer for.
            answer (str): Answer to the question.

        Returns:
            bool: True if the answer is correct, False otherwise.
        """

        # TODO: Implement answer checking

        pass


    
