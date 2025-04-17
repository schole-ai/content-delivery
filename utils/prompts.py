
def create_prompt(docs, question_type, level, prompt_type="basic"):
    """
    Construct the prompt for the LLM to generate a question based on Bloom's Taxonomy.

    Args:
        docs (list): List of documents containing text and images.
        question_type (str): Type of question to generate, e.g., multiple-choice (MCQ), short answer (SAQ).
        level (str): Bloom's Taxonomy level for cognitive complexity.
        prompt_type (str): Type of prompt to use, e.g., basic or description.

    Returns:
        tuple: System and user prompts
    """

    assert question_type in ["MCQ", "SAQ"], "Invalid question type. Options are 'MCQ' or 'SAQ'."

    task_prompt = get_task_prompt(question_type)
    output_format_prompt = get_output_format(question_type)

    system_prompt = "You are a highly skilled AI tutor specializing in education and Bloom's Taxonomy."

    text_docs = [doc for doc in docs if doc.metadata["type"] == "text"]
    img_docs = [doc for doc in docs if doc.metadata["type"] == "image"]
    context_text = ""

    if len(text_docs) > 0:
        context_text = "\n".join([doc.page_content for doc in text_docs])

    if prompt_type == "basic":
        # Basic prompt, only specify the task
        prompt_template = (
            f"{task_prompt}"
            f"The Bloom's Taxonomy level for cognitive complexity is: {level}. "
            "Make sure the question is relevant to the context and is at the correct Bloom's Taxonomy level. "
            "The question should be naturally phrased and fully self-contained, without explicitly referencing the context (e.g., avoid phrases like 'according to the text' or 'in the provided text'). "
            f"{output_format_prompt}\n"
            f"Context: {context_text}\n"
        )

    elif prompt_type == "desc":
        # More detailed prompt where we provide the description of each Bloom's Taxonomy level
        prompt_template = (
            f"{task_prompt}"
            f"The Bloom's Taxonomy level for cognitive complexity is: {level}. The description of the level is: "
            f"{get_bloom_level_prompt(level)}. "
            "Make sure the question is relevant to the context and is at the correct Bloom's Taxonomy level. "
            "The question should be naturally phrased and fully self-contained, without explicitly referencing the context (e.g., avoid phrases like 'according to the text' or 'in the provided text'). "
            f"{output_format_prompt}\n"
            f"Context: {context_text}\n"
        )
    
    elif prompt_type == "desc_examples":
        # More detailed prompt where we provide the description of each Bloom's Taxonomy level with examples
        # Examples come from https://whatfix.com/blog/blooms-taxonomy/
        prompt_template = (
            f"{task_prompt}"
            f"The Bloom's Taxonomy level for cognitive complexity is: {level}. The description of the level is: "
            f"{get_bloom_level_prompt(level)}. "
            f"Examples of questions at this level are: {get_bloom_level_examples(level)}. "
            "Make sure the question is relevant to the context and is at the correct Bloom's Taxonomy level. "
            "The question should be naturally phrased and fully self-contained, without explicitly referencing the context (e.g., avoid phrases like 'according to the text' or 'in the provided text'). "
            f"{output_format_prompt}\n"
            f"Context: {context_text}\n"
        )

    prompt_content = [{"type": "text", "text": prompt_template}]

    if len(img_docs) > 0:
        for img in img_docs:
            prompt_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img.page_content}"},
                }
            )

    return system_prompt, prompt_content


def create_refine_prompt(docs, question, question_type, gt_level, pred_level):
    """
    Construct the prompt for the LLM to refine a question based on Bloom's Taxonomy.

    Args:
        text (str): Text snippet from the course material.
        question (str): Question to refine.
        question_type (str): Type of question to generate, e.g., multiple-choice (MCQ), short answer (SAQ).
        gt_level (str): Ground truth Bloom's Taxonomy level for cognitive complexity.
        pred_level (str): Predicted Bloom's Taxonomy level for cognitive complexity.

    Returns:
        tuple: System and user prompts
    """

    assert question_type in ["MCQ", "SAQ"], "Invalid question type. Options are 'MCQ' or 'SAQ'."
    assert gt_level in ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"], "Invalid Bloom's Taxonomy level."
    assert pred_level in ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"], "Invalid Bloom's Taxonomy level."

    if question_type == "MCQ":
        question_type_prompt = "You have to keep the question as a multiple-choice question with four answer choices (A, B, C, D), with only one correct answer. "
    elif question_type == "SAQ":
        question_type_prompt = "You have to keep the question as a short answer question. "

    system_prompt = "You are a highly skilled AI tutor specializing in education and Bloom's Taxonomy."

    text_docs = [doc for doc in docs if doc.metadata["type"] == "text"]
    img_docs = [doc for doc in docs if doc.metadata["type"] == "image"]
    context_text = ""

    if len(text_docs) > 0:
        context_text = "\n".join([doc.page_content for doc in text_docs]) 

    prompt_template = (
        "You are given a generated question based on a context from a student's course material which is at the wrong Bloom's Taxonomy level. "
        f"The question has been predicted to be at the level: {pred_level}. "
        f"The expected level is: {gt_level}. "
        "Your task is to refine the question to be at the correct Bloom's Taxonomy level. "
        f"{question_type_prompt}"
        "You are provided with a context that may include text or images from the course material, as well as the generated question. "
        "The question should keep a natural phrasing and be fully self-contained, without explicitly referencing the context (e.g., avoid phrases like 'according to the text' or 'in the provided text'). "
        f"{get_output_format(question_type)}\n"
        f"Wrongly classified question: {question}\n"
        f"Context: {context_text}\n"
    )    

    prompt_content = [{"type": "text", "text": prompt_template}]

    if len(img_docs) > 0:
        for img in img_docs:
            prompt_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img.page_content}"},
                }
            )


    return system_prompt, prompt_content


def create_judge_prompt(docs, question, answer):
    """
    Construct the prompt for the LLM to judge a student's answer.

    Args:
        docs (list): List of documents containing text and images.
        question (str): Question to judge.
        answer (str): Student's answer.

    Returns:
        tuple: System and user prompts
    """

    system_prompt = "You are a highly skilled AI tutor."

    text_docs = [doc for doc in docs if doc.metadata["type"] == "text"]
    img_docs = [doc for doc in docs if doc.metadata["type"] == "image"]
    context_text = ""

    if len(text_docs) > 0:
        context_text = "\n".join([doc.page_content for doc in text_docs]) 

    prompt_template = (
        "You are given a question based on a context that may include text or images from a student's course material and the student's answer. "
        "Your task is to determine if the answer is correct or incorrect and provide a short feedback to the student. "
        "Your answer should not explicitly reference the context (e.g., avoid phrases like 'according to the text' or 'in the provided text'). "
        "Respond ONLY with a valid JSON object. DO NOT wrap the JSON in triple backticks or any other formatting. The JSON must contain: \n" 
        "{\n"
        "  \"is_correct\": true/false,\n"
        "  \"feedback\": \"<feedback to the student>\"\n"
        "}\n"
        f"Question: {question}\n"
        f"Student Answer: {answer}\n"
        f"Context: {context_text}\n"
    )

    prompt_content = [{"type": "text", "text": prompt_template}]

    if len(img_docs) > 0:
        for img in img_docs:
            prompt_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img.page_content}"},
                }
            )

    return system_prompt, prompt_content

def get_task_prompt(question_type):
    """
    Get the task prompt based on the question type.

    Args:
        question_type (str): Type of question to generate, e.g., multiple-choice (MCQ), short answer (SAQ).

    Returns:
        str: The task prompt for the specified question type.
    """

    if question_type == "MCQ":
        prompt = (
            "Your task is to generate a well-structured, pedagogically sound multiple-choice question based on a given context, which may include text or images from a student's course material. "
            "The multiple-choice question should have four answer choices (A, B, C, D), with only one correct answer. "
        )
        
    elif question_type == "SAQ":
        prompt = (
            "Your task is to generate a well-structured, pedagogically sound short answer question based on a given context, which may include text or images from a student's course material. "
        )
    
    return prompt


def get_output_format(question_type):
    """
    Get the output format based on the question type.

    Args:
        question_type (str): Type of question to generate, e.g., multiple-choice (MCQ), short answer (SAQ).

    Returns:
        str: The output format for the specified question type.
    """

    if question_type == "MCQ":
        prompt = (
            "Respond ONLY with a valid JSON object. DO NOT wrap the JSON in triple backticks or any other formatting. The JSON must contain: \n"  
            "{\n"
            "  \"question\": \"<full text question>\",\n"
            "  \"choices\": {\n"
            "    \"A\": \"<choice A>\",\n"
            "    \"B\": \"<choice B>\",\n"
            "    \"C\": \"<choice C>\",\n"
            "    \"D\": \"<choice D>\"\n"
            "  },\n"
            "  \"answer\": \"<correct letter>\"\n"
            "}"
        )
        
    elif question_type == "SAQ":
        prompt = (
            "Respond ONLY with a valid JSON object. DO NOT wrap the JSON in triple backticks or any other formatting. The JSON must contain: \n" 
            "{\n"
            "  \"question\": \"<full text question>\",\n"
            "  \"correct_answer\": \"<a possible correct answer>\"\n"
            "  \"incorrect_answer\": \"<a possible incorrect answer>\"\n"
            "}"
        )
    
    return prompt


def get_bloom_level_prompt(level):
    """
    Get the prompt for a specific Bloom's Taxonomy level.

    Args:
        level (str): The Bloom's Taxonomy level.

    Returns:
        str: The prompt for the specified Bloom's Taxonomy level.
    """

    assert level in ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"], "Invalid Bloom's Taxonomy level."

    levels = {
        "Remember": "Retrieve relevant knowledge from long-term memory.",
        "Understand": "Determine the meaning of instructional messages, including oral, written, and graphic communication.",
        "Apply": "Carry out or use a procedure in a given situation.",
        "Analyze": "Break material into its constituent parts and detect how the parts relate to one another and to an overall structure or purpose.",
        "Evaluate": "Make judgments based on criteria and standards.",
        "Create": "Put elements together to form a novel, coherent whole or make an original product."
    }
    
    return levels.get(level)

def get_bloom_level_examples(level):
    """
    Get examples for a specific Bloom's Taxonomy level.

    Args:
        level (str): The Bloom's Taxonomy level.

    Returns:
        str: Examples for the specified Bloom's Taxonomy level.
    """

    assert level in ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"], "Invalid Bloom's Taxonomy level."

    examples = {
        "Remember": "\"Can you name our company's five top product offerings?\", \"What application do we use to monitor progress?\", \"What are our organization's core values?\"",
        "Understand": "\"Explain why it is important to file an incident report\", \"How would you explain this policy to a customer?\", \"How would you explain this policy to a customer?\"",
        "Apply": "\"How would you update the status of this project in our system?\", \"Can you walk us through the process of creating a ticket for this issue?\", \"Can you determine how much a client owes on their contract given these account details?\"",
        "Analyze": "\"What is the motivation behind this policy?\", \"What conclusions can you draw from comparing these annual reports?\", \"What assumptions do we have to make when creating a care plan for this client?\"",
        "Evaluate": "\"What criteria can you use to evaluate the success of this type of project?\", \"Can you find the error in this example response to a frustrated customer?\", \"What are the pros and cons of these different approaches?\"",
        "Create": "\"Can you design an ad campaign for this hypothetical client?\", \"How would you create a plan for this type of emergency?\", \"What changes would you make to this example contract?\""
    }
    
    return examples.get(level)
