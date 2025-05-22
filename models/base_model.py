import torch
class BaseModel():
    def __init__(self, config):
        """
        Base model constructor to initialize common attributes.
        :param config: A dictionary containing model configuration parameters.
        """
        self.config = config
        
    def predict(self, question, texts = None, images = None, history = None):
        pass
    
    def clean_up(self):
        torch.cuda.empty_cache()
        
    def process_message(self, question, texts, images, history):
        if history is not None:
            assert(self.is_valid_history(history))
            messages = history
        else:
            messages = []
        
        if texts is not None:
            messages.append(self.create_text_message(texts, question))
        if images is not None:
            messages.append(self.create_image_message(images, question))
        
        if (texts is None or len(texts) == 0) and (images is None or len(images) == 0):
            messages.append(self.create_ask_message(question))
        
        return messages
    
    def is_valid_history(self, history):
        return True