import random

QUESTION_TYPES = ["MCQ", "SAQ"]
BLOOM_MAP = {"remember": 1, "understand": 2, "apply": 3, "analyze": 4, "evaluate": 5, "create": 6}
BLOOM_MAP_REVERSE = {v: k for k, v in BLOOM_MAP.items()}

class LearningTracker:
    """Class to track the learning progress of a user."""
    def __init__(self, 
                 session_id, 
                 prolific_id=None, 
                 strategy="default", 
                 min_success_question=2, 
                 max_fail_question=2, 
                 init_bloom_level=None, 
                 supabase=None):
        
        self.session_id = session_id
        self.prolific_id = prolific_id
        self.strategy = strategy    # strategy to change the level, can be "default", "revert" or "random"
        self.init_bloom_level = init_bloom_level
        self.min_success_question = min_success_question # minimum number of questions to be answered correctly at each level before moving to the next level
        self.max_fail_question = max_fail_question # maximum number of questions to be answered incorrectly at each level before moving back to the previous level
        self.current_level = None
        self.logs = self.initialize_logs()
        self.supabase = supabase  # Supabase client for storing logs

    
    def initialize_logs(self):
        return {
            "session_id": self.session_id,
            "prolific_id": self.prolific_id,
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
            "rating": None,
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

    def update_rating(self, rating):
        """Update the rating."""
        self.logs["rating"] = rating

    def post_logs(self):
        """Post the logs to the Supabase database."""
        if not self.supabase:
            raise ValueError("Supabase client is not initialized.")
        
        # Post the logs to the Supabase database
        response = self.supabase.table("feedback").upsert(self.logs, on_conflict=["session_id"]).execute()
        return response
        

    def get_next_bloom_level(self):
        """Get the next bloom level based on the strategy."""
        if self.current_level is None:
            self.current_level = self._initial_level()
            return self.current_level
        
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
        if self.init_bloom_level is not None:
            return self.init_bloom_level
        
        if self.strategy == "default":
            return 1
        elif self.strategy == "revert":
            return 6
        elif self.strategy == "random":
            return random.randint(1, 6)
        else:
            raise ValueError("Invalid strategy.")
    
    def _consecutive_successes(self):
        """Calculate the number of consecutive successes at the current level."""
        history = self.logs["history"]
        successes = 0
        for entry in reversed(history):
            if entry["level"] == self.current_level and entry["is_correct"]:
                successes += 1
            else:
                break
        return successes
    
    def _consecutive_failures(self):
        """Calculate the number of consecutive failures at the current level."""
        history = self.logs["history"]
        failures = 0
        for entry in reversed(history):
            if entry["level"] == self.current_level and not entry["is_correct"]:
                failures += 1
            else:
                break
        return failures

    def _handle_default_strategy(self):
        """
        Set the current level based on the default strategy (1 to 6).: 
        If the consecutive successes at the current level are greater than or equal to the minimum number of successes, move to the next level.
        If the consecutive failures at the current level are greater than or equal to the maximum number of failures, move to the previous level.
        """
        if self._consecutive_successes() >= self.min_success_question:
            if self.current_level < 6:
                self.current_level += 1
        elif self._consecutive_failures() >= self.max_fail_question:
            if self.current_level > 1:
                self.current_level -= 1
        else:
            self.current_level = self.current_level
                    

    def _handle_revert_strategy(self):
        """
        Set the current level based on the revert strategy (6 to 1).:
        If the consecutive failures at the current level are greater than or equal to the maximum number of failures, move to the next level.
        If the consecutive successes at the current level are greater than or equal to the minimum number of successes, move to the previous level.
        """
        if self._consecutive_successes() >= self.min_success_question:
            if self.current_level > 1:
                self.current_level -= 1
        elif self._consecutive_failures() >= self.max_fail_question:
            if self.current_level < 6:
                self.current_level += 1
        else:
            self.current_level = self.current_level


    def _handle_random_strategy(self):
        """
        Set the current level based on the random strategy (1 to 6).:
        If the consecutive successes or failures at the current level are greater than or equal to the minimum number of successes or maximum number of failures, move to a random level.
        """
        if self._consecutive_successes() >= self.min_success_question or self._consecutive_failures() >= self.max_fail_question:
            self.current_level = random.randint(1, 6)
        else:
            self.current_level = self.current_level

    def get_question_type(self):
        """Set the question type."""
        return random.choice(QUESTION_TYPES)



