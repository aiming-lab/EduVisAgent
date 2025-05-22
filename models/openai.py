from models.base_model import BaseModel
from openai import OpenAI
import base64
import os

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

class MyOpenAI(BaseModel):
    def __init__(self, config):
        super().__init__(config)
        self.model = self.config.model
        self.client = OpenAI(
            api_key=self.config.api_key,  # This is the default and can be omitted
        )
        self.create_ask_message = lambda question: {
            "role": "user",
            "content": [
                {"type": "text", "text": question},
            ],
        }
        
    def create_text_message(self, texts, question): 
        prompt = ""
        for text in texts:
            prompt = prompt + text + '\n'
        message = {
            "role": "user",
            "content": [
                {"type": "text", "text": f"{prompt}\n{question}"},
            ]
        }
        return message
    
    def create_image_message(self, images, question):
        content = []
        for image in images:
            if os.path.exists(image):
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(image)}"},},)
        content.append({"type": "text", "text": question},)
        message = {
            "role": "user",
            "content": content
        }
        return message
    
    def create_ans_message(self, answer):
        return {
            "role": "assistant",
            "content": [
                {"type": "text", "text": answer},
            ],
        }
        
    def predict(self, question, texts = None, images = None, history = None):
        messages = self.process_message(question, texts, images, history)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.config.max_new_tokens,
        )
        result = response.choices[0].message.content
        messages.append(self.create_ans_message(result))
        return result, messages
    
    def is_valid_history(self, history):
        if not isinstance(history, list):
            return False
        for item in history:
            if not isinstance(item, dict):
                return False
            if "role" not in item or "content" not in item:
                return False
            if not isinstance(item["role"], str) or not isinstance(item["content"], list):
                return False
            for content in item["content"]:
                if not isinstance(content, dict):
                    return False
                if "type" not in content:
                    return False
                if content["type"] not in content:
                    return False
        return True
    