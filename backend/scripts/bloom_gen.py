import os
import json
import requests
import sys
import random

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))

from copy import deepcopy
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from ..utils.prompts import create_prompt, create_refine_prompt, create_judge_prompt
from ..utils.helpers import clean_pdf_text
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BLOOM_TAXONOMY = {1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze", 5: "Evaluate", 6: "Create"}
BLOOM_BERT_MAP = {"Remember": 1, "Understand": 2, "Apply": 3, "Analyse": 4, "Evaluate": 5, "Create": 6}

# URL for BloomBERT API (https://github.com/RyanLauQF/BloomBERT?tab=readme-ov-file)
BLOOM_BERT_URL = "https://bloom-bert-api-dmkyqqzsta-as.a.run.app/predict"


class BloomQuestionGenerator:
    """Class to generate questions based on Bloom's Taxonomy"""
    def __init__(self, model="gpt-4o"):
        self.model = model # Use "gpt-4o" to have multimodal capabilities
        self.llm = ChatOpenAI(
            model_name=self.model,
            temperature=0.5,
            openai_api_key=OPENAI_API_KEY,
        )
    

    def generate_question(self, docs, question_type="MCQ", level=1, prompt_type="basic", refine=False):
        """
        Generate a question from a chunk based on Bloom's Taxonomy.

        Args:
            docs (list): List of documents to generate questions from.
            question_type (str): Type of question to generate. Options are "MCQ" or "SAQ".
            level (int): Bloom's Taxonomy level to generate questions from.
            prompt_type (str): Type of prompt to use. Options are "basic" or "description".
            refine (bool): Whether to refine the question if it is not correctly classified by Bloom's Taxonomy.
        
        Returns:
            str: Generated question.
        """

        assert question_type in ["MCQ", "SAQ"], "Invalid question type. Options are 'MCQ' or 'SAQ."
        assert level in range(1, 7), "Invalid Bloom's Taxonomy level. Level should be between 1 and 6."

        system_msg, prompt_content = create_prompt(docs, question_type, BLOOM_TAXONOMY[level], prompt_type)
       
        chat_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_msg),
                HumanMessage(content=prompt_content)
            ]
        )
        
        valid = False # Flag to check if the generated question follows the correct format (see sanity_check method)

        while not valid:
            response = self.llm.invoke(chat_template.format_messages())
            question_dict = response.content
            question_dict = clean_pdf_text(question_dict)
            valid = self.sanity_check(question_dict, question_type)

        question_dict = json.loads(question_dict)

        if refine:
            question = question_dict["question"]
            pred_level, is_correct = self.evaluate_question(question, level)
            if not is_correct:
                print(f"Refining question: {question} (predicted level: {pred_level}, ground truth level: {level})")
                if question_type == "MCQ":
                    # concatenate the question with the answer options
                    question = question_dict["question"] + "\n"
                    for letter, answer in question_dict["choices"].items():
                        question += f"{letter}: {answer}\n"
                    
                question_dict = self.refine_question(question, docs, pred_level, level, question_type)

        # if the question type is MCQ, shuffle the answer options to make sure the correct answer is not always in the same position due to the prompt
        if question_type == "MCQ":
            question_dict = self.shuffle_mcq(question_dict)

        return question_dict
    

    def refine_question(self, question, docs, pred_level, gt_level, question_type="MCQ"):
        """
        Refine a generated question which has been not correctly classified by Bloom's Taxonomy with BloomBERT.

        Args:
            question (str): Question to refine.
            docs (list): List of documents to generate questions from.
            pred_level (int): Predicted Bloom's Taxonomy level.
            gt_level (int): Ground truth Bloom's Taxonomy level.
            question_type (str): Type of question to generate. Options are "MCQ" or "SAQ".
        
        Returns:
            str: Refined question.
        """

        system_msg, prompt_content = create_refine_prompt(docs, question, question_type, BLOOM_TAXONOMY[gt_level], BLOOM_TAXONOMY[pred_level])

        chat_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_msg),
                HumanMessage(content=prompt_content)
            ]
        )

        valid = False

        while not valid:
            response = self.llm.invoke(chat_template.format_messages())
            refined_question_dict = response.content
            refined_question_dict = clean_pdf_text(refined_question_dict)
            valid = self.sanity_check(refined_question_dict, question_type)

        refined_question_dict = json.loads(refined_question_dict)

        return refined_question_dict
    

    def shuffle_mcq(self, question_dict):
        """
        Shuffle the answer options of a multiple choice question.

        Args:
            question_dict (dict): Dictionary containing the question and answer options.

        Returns:
            dict: Dictionary with shuffled answer options.
        """
        new_qdict = deepcopy(question_dict)

        correct_text = question_dict['choices'][question_dict['answer']]
        all_texts = list(question_dict['choices'].values())
        random.shuffle(all_texts)

        letters = ["A", "B", "C", "D"]
        new_choices = dict(zip(letters, all_texts))

        for letter, text in new_choices.items():
            if text == correct_text:
                new_qdict['answer'] = letter
                break

        new_qdict['choices'] = new_choices
        return new_qdict
    

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

            predicted_level = BLOOM_BERT_MAP.get(response_dict.get("blooms_level"))

            return predicted_level, predicted_level == level

        except Exception as e:
            print(f"Error: {e}")
            return False        


    def check_answer_saq(self, docs, question, answer):
        """
        Check if the answer to a short answer question is correct.

        Args:
            docs (list): List of documents to check the answer against.
            question (str): Question to check the answer for.
            answer (str): User answer to the question.

        Returns:
            tuple: (bool, str): Tuple containing a boolean indicating if the answer is correct and feedback.
        """

        system_msg, prompt_content = create_judge_prompt(docs, question, answer)

        chat_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=system_msg),
                HumanMessage(content=prompt_content)
            ]
        )
            
        valid = False

        while not valid:
            response = self.llm.invoke(chat_template.format_messages())
            correction_dict_str = response.content
            correction_dict_str = clean_pdf_text(correction_dict_str)
            valid = self.sanity_check_judge(correction_dict_str)
        
        correction_dict = json.loads(correction_dict_str)

        return correction_dict["is_correct"], correction_dict["feedback"]
    

    def check_answer_mcq(self, question_dict, answer):
        """
        Check if the answer to a multiple choice question is correct.

        Args:
            question_dict (dict): Dictionary containing the question and answer options.
            answer (str): User answer to the question.

        Returns:
            bool: True if the answer is correct, False otherwise.
        """

        assert answer in ["A", "B", "C", "D"], "Answer is not one of the answer options."

        return question_dict["answer"] == answer
    

    def sanity_check(self, question_dict_str, question_type):
        """
        Perform a sanity check on the generated question.

        Args:
            question_dict_str (str): Generated question in string format.
            question_type (str): Type of question to generate. Options are "MCQ" or "SAQ".

        Returns:
            bool: True if the question is valid, False otherwise.
        """

        try:
            question_dict = json.loads(question_dict_str)
        except json.JSONDecodeError:
            print("Error decoding JSON string.")
            print(f"Generated string: {question_dict_str}")
            print("Raw:", repr(question_dict_str))
            return False

        try:
            assert isinstance(question_dict, dict), "Question is not a dictionary."
            assert "question" in question_dict, "Question is missing."
            assert isinstance(question_dict["question"], str), "Question is not a string."
            assert len(question_dict["question"]) > 0, "Question is empty."
            
            if question_type == "MCQ":
                assert "choices" in question_dict, "Choices are missing."
                assert len(question_dict["choices"]) == 4, "Number of answer options is not 4."
                assert "A" in question_dict["choices"], "Answer option A is missing."
                assert "B" in question_dict["choices"], "Answer option B is missing."
                assert "C" in question_dict["choices"], "Answer option C is missing."
                assert "D" in question_dict["choices"], "Answer option D is missing."
                assert "answer" in question_dict, "Answer is missing."
                assert question_dict["answer"] in ["A", "B", "C", "D"], "Answer is not one of the answer options."
                assert all(isinstance(choice, str) for choice in question_dict["choices"].values()), "Answer options are not strings."
            
            elif question_type == "SAQ":
                assert "correct_answer" in question_dict, "Answer is missing."
                assert "incorrect_answer" in question_dict, "Incorrect answer is missing."
                assert isinstance(question_dict["correct_answer"], str), "Correct answer is not a string."
                assert isinstance(question_dict["incorrect_answer"], str), "Incorrect answer is not a string."
                assert len(question_dict["correct_answer"]) > 0, "Correct answer is empty."
                assert len(question_dict["incorrect_answer"]) > 0, "Incorrect answer is empty."
            
            return True
        
        except AssertionError as e:
            print(f"Sanity check failed: {e}")
            print(f"Generated string: {question_dict_str}")
            return False
        

    def sanity_check_judge(self, correction_dict_str):
        """
        Perform a sanity check on the generated correction.

        Args:
            correction_dict_str (str): Generated correction in string format.

        Returns:
            bool: True if the correction is valid, False otherwise.
        """

        try:
            correction_dict = json.loads(correction_dict_str)
        except json.JSONDecodeError:
            print("Error decoding JSON string.")
            print(f"Generated string: {correction_dict_str}")
            return False

        try:
            assert isinstance(correction_dict, dict), "Correction is not a dictionary."
            assert "is_correct" in correction_dict, "is_correct is missing."
            assert isinstance(correction_dict["is_correct"], bool), "is_correct is not a boolean."
            assert "feedback" in correction_dict, "Feedback is missing."
            assert isinstance(correction_dict["feedback"], str), "Feedback is not a string."
            
            return True
        
        except AssertionError as e:
            print(f"Sanity check failed: {e}")
            print(f"Generated string: {correction_dict_str}")
            return False