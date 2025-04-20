import random

QUESTION_TYPES = ["MCQ", "SAQ"]
BLOOM_MAP = {"remember": 1, "understand": 2, "apply": 3, "analyze": 4, "evaluate": 5, "create": 6}
BLOOM_MAP_REVERSE = {v: k for k, v in BLOOM_MAP.items()}

class LearningTracker:
    """Class to track the learning progress of a user."""
    def __init__(self, id, strategy="default", min_question_per_level=2, until_success=False):
        self.id = id
        self.strategy = strategy    # strategy to change the level, can be "default", "revert" or "random"
        self.min_question_per_level = min_question_per_level # minimum number of questions to be answered at each level before moving to the next level, 
                                                             # if until_success is True, this is the minimum number of questions answered correctly 
                                                             # at each level before moving to the next level
        self.until_success = until_success # change the level only if the user answers the question correctly
        self.loop_count = 0 # number of times the user has looped through the levels
        self.current_level = None
        self.logs = self.initialize_logs()

    
    def initialize_logs(self):
        return {
            "id": self.id,
            "strategy": self.strategy,
            "total_questions_answered": 0,
            "total_questions_correct": 0,
            "total_mcq_answered": 0,
            "total_mcq_correct": 0,
            "total_saq_answered": 0,
            "total_saq_correct": 0,
            "bloom": {
                "total_questions_answered_per_level": {
                    "remember": 0,
                    "understand": 0,
                    "apply": 0,
                    "analyze": 0,
                    "evaluate": 0,
                    "create": 0,
                },
                "total_questions_correct_per_level": {
                    "remember": 0,
                    "understand": 0,
                    "apply": 0,
                    "analyze": 0,
                    "evaluate": 0,
                    "create": 0,
                }
            },
            "history": [], 
        }
    
    def get_logs(self):
        return self.logs
    
    def update_logs(self, question_type, is_correct, level, elapsed_time, question, answer):
        """Update the logs with the question type, whether the answer was correct, the level, elapsed time, question and answer."""
        self.logs["total_questions_answered"] += 1
        self.logs["bloom"]["total_questions_answered_per_level"][BLOOM_MAP_REVERSE[level]] += 1
        
        if question_type == "MCQ":
            choices = question["choices"]
            correct_answer = question["answer"]
            question = question["question"]
        elif question_type == "SAQ":
            choices = None
            correct_answer = None
            
        self.logs["history"].append({
            "question_type": question_type,
            "question": question,
            "choices": choices,
            "correct_answer": correct_answer,
            "user_answer": answer,
            "is_correct": is_correct,
            "level": level,
            "elapsed_time": elapsed_time,
        })

        if is_correct:
            self.logs["total_questions_correct"] += 1
            self.logs["bloom"]["total_questions_correct_per_level"][BLOOM_MAP_REVERSE[level]] += 1

        if question_type == "MCQ":
            self.logs["total_mcq_answered"] += 1
            if is_correct:
                self.logs["total_mcq_correct"] += 1
        elif question_type == "SAQ":
            self.logs["total_saq_answered"] += 1
            if is_correct:
                self.logs["total_saq_correct"] += 1
        

    def get_next_bloom_level(self):
        """Get the next bloom level based on the strategy."""
        if self.current_level is None:
            self.current_level = self._initial_level()
            return self.current_level

        total_questions_valid = self._get_total_questions_valid()

        # Set the threshold for the number of questions to be answered (correctly if until_succes is True) at each level before moving to the next level
        threshold = self.min_question_per_level + self.loop_count * self.min_question_per_level 

        if total_questions_valid >= threshold:
            if self.strategy == "default":
                self._handle_default_strategy()
            elif self.strategy == "revert":
                self._handle_revert_strategy()
            elif self.strategy == "random":
                self._handle_random_strategy()
            else:
                raise ValueError("Invalid strategy.")

        return self.current_level
    
    def _initial_level(self):
        """Set the initial level for the different strategies."""	
        if self.strategy == "default":
            return 1
        elif self.strategy == "revert":
            return 6
        elif self.strategy == "random":
            return random.randint(1, 6)
        else:
            raise ValueError("Invalid strategy.")
        
    def _get_total_questions_valid(self):
        """Get the total number of questions answered at the current level. Only considers correct answers if until_success is True."""
        key = "total_questions_correct_per_level" if self.until_success else "total_questions_answered_per_level"
        return self.logs["bloom"][key][BLOOM_MAP_REVERSE[self.current_level]]

    def _handle_default_strategy(self):
        """Set the current level to the next level. If the current level is 6, set it to 1."""
        if self.current_level < 6:
            self.current_level += 1
        else:
            self.current_level = 1
            self.loop_count += 1

    def _handle_revert_strategy(self):
        """Set the current level to the previous level. If the current level is 1, set it to 6."""
        if self.current_level > 1:
            self.current_level -= 1
        else:
            self.current_level = 6
            self.loop_count += 1

    def _handle_random_strategy(self):
        """Set the current level to a random level between 1 and 6."""
        self.current_level = random.randint(1, 6)
        self.loop_count += 1

    def get_question_type(self):
        """Set the question type."""
        return random.choice(QUESTION_TYPES)



