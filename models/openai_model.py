import os
from openai import OpenAI
from dotenv import load_dotenv
from .base_model import BaseModel # Assuming BaseModel is in the same directory

class OpenAIModel(BaseModel):
    def __init__(self, config):
        super().__init__(config)
        load_dotenv() # Load environment variables from .env file
        
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it in your .env file.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model_id = config.model_id
        self.temperature = getattr(config, 'temperature', 0.7)
        self.max_tokens = getattr(config, 'max_tokens', 2048)

    def predict(self, question: str, texts: list = None, images: list = None, history: list = None):
        """
        Predicts an answer to a question using the OpenAI API.

        Args:
            question (str): The question to ask the model. (This will include the system prompt from BaseAgent)
            texts (list, optional): Additional text context. Not directly used by standard OpenAI chat models in this basic predict.
            images (list, optional): Image context. Not used by standard OpenAI chat models in this basic predict.
            history (list, optional): A list of previous messages in OpenAI's format 
                                      (e.g., [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]).

        Returns:
            tuple: (generated_answer_string, updated_message_history_list)
        """
        messages = []
        if history:
            messages.extend(history)
        
        # The BaseAgent's predict method prepends the system_prompt from agent config to the question.
        # So, the `question` arg here will contain that combined string.
        # For OpenAI, the system prompt ideally is a separate message with role: system.
        # However, BaseAgent passes it concatenated. For now, we pass the whole string as user content.
        # A more advanced BaseAgent/OpenAIModel could split this.
        messages.append({"role": "user", "content": question}) 

        try:
            completion = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            assistant_response = completion.choices[0].message.content
            # Add assistant response to history for next turn
            messages.append({"role": "assistant", "content": assistant_response})
            return assistant_response, messages
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return f"Error: Could not get a response from OpenAI. Details: {str(e)}", messages

    def predict_batch(self, prompts: list, **kwargs):
        # This is a simplified sequential implementation for batch prediction.
        # True batching with OpenAI typically involves async calls or managing multiple requests.
        results = []
        for prompt_data in prompts:
            if isinstance(prompt_data, str):
                q = prompt_data
                h = None
            else: # Assuming dict from BaseModel's default predict_batch
                q = prompt_data.get('question')
                h = prompt_data.get('history')
            
            answer, _ = self.predict(question=q, history=h)
            results.append(answer)
        return results
