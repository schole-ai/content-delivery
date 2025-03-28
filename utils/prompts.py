
def create_prompt(text, question_type, level, prompt_type="basic"):
    """
    Construct the prompt for the LLM to generate a question based on Bloom's Taxonomy.

    Args:
        text (str): Text snippet from the course material.
        question_type (str): Type of question to generate, e.g., multiple-choice (MCQ), short answer (SAQ).
        level (str): Bloom's Taxonomy level for cognitive complexity.
        prompt_type (str): Type of prompt to use, e.g., basic or description.

    Returns:
        tuple: System and user prompts
    """

    assert question_type in ["MCQ", "SAQ"], "Invalid question type. Options are 'MCQ' or 'SAQ'."

    task_prompt = get_task_prompt(question_type)

    if prompt_type == "basic":
        # Basic prompt, only specify the task
        context_system = (
            "You are a highly skilled AI tutor specializing in education and Bloom's Taxonomy. "
            f"{task_prompt}"
            "You will be provided with: "
            "- A text snippet from the course. "
            "- The Bloom's Taxonomy level for cognitive complexity. "
            "Make sure the question is relevant to the text and is at the correct Bloom's Taxonomy level. "
            "The question should be naturally phrased and fully self-contained, without explicitly referencing the text snippet (e.g., avoid phrases like 'according to the text' or 'in the provided text'). "
            "Only output the question."
        )

    elif prompt_type == "desc":
        # More detailed prompt where we provide the description of each Bloom's Taxonomy level
        context_system = (
            "You are a highly skilled AI tutor specializing in education and Bloom's Taxonomy. "
            f"{task_prompt}"
            "You will be provided with: "
            "- A text snippet from the course. "
            "- The Bloom's Taxonomy level for cognitive complexity. "
            "Here are the Bloom's Taxonomy levels for reference: "
            "1. Remember: Retrieve relevant knowledge from long-term memory. "
            "2. Understand: Determining the meaning of instructional messages, including oral, written, and graphic communication. "
            "3. Apply: Carrying out or using a procedure in a given situation. "
            "4. Analyze: Breaking material into its constituent parts and detecting how the parts relate to one another and to an overall structure or purpose. "
            "5. Evaluate: Making judgments based on criteria and standards. "	
            "6. Create: Putting elements together to form a novel, coherent whole or make an original product. "
            "Make sure the question is relevant to the text and is at the correct Bloom's Taxonomy level. "
            "The question should be naturally phrased and fully self-contained, without explicitly referencing the text snippet (e.g., avoid phrases like 'according to the text' or 'in the provided text'). "
            "Only output the question."
        )
    
    elif prompt_type == "desc_examples":
        # More detailed prompt where we provide the description of each Bloom's Taxonomy level with examples
        # Examples come from https://whatfix.com/blog/blooms-taxonomy/
        context_system = (
            "You are a highly skilled AI tutor specializing in education and Bloom's Taxonomy. "
            f"{task_prompt}"
            "You will be provided with: "
            "- A text snippet from the course. "
            "- The Bloom's Taxonomy level for cognitive complexity. "
            "Here are the Bloom's Taxonomy levels and examples for reference: "
            "1. Remember: Retrieve relevant knowledge from long-term memory. Example: Can you name our company's five top product offerings? "
            "2. Understand: Determining the meaning of instructional messages, including oral, written, and graphic communication. Example: How would you explain this policy to a customer? "
            "3. Apply: Carrying out or using a procedure in a given situation. Example: How would you update the status of this project in our system? "
            "4. Analyze: Breaking material into its constituent parts and detecting how the parts relate to one another and to an overall structure or purpose. Example: What conclusions can you draw from comparing these annual reports? "
            "5. Evaluate: Making judgments based on criteria and standards. Example: What criteria can you use to evaluate the success of this type of project? "	
            "6. Create: Putting elements together to form a novel, coherent whole or make an original product. Example: Can you design an ad campaign for this hypothetical client? "
            "Make sure the question is relevant to the text and is at the correct Bloom's Taxonomy level. "
            "The question should be naturally phrased and fully self-contained, without explicitly referencing the text snippet (e.g., avoid phrases like 'according to the text' or 'in the provided text'). "
            "Only output the question."
        )


    context_user = (
        f"Text: {text}\n"
        f"Bloom's Taxonomy Level: {level}\n"
        "Question:"
    )

    return context_system, context_user


def get_task_prompt(question_type):
    if question_type == "MCQ":
        prompt = (
            "Your task is to generate a well-structured, pedagogically sound multiple-choice question based on a given text snippet from a student's course material. "
            "The multiple-choice question should have four answer choices (A, B, C, D), with only one correct answer. "
        )
        
    elif question_type == "SAQ":
        prompt = (
            "Your task is to generate a well-structured, pedagogically sound short answer question based on a given text snippet from a student's course material. "
        )
    
    return prompt
    
