from models.base_model import BaseModel
from mydatasets.doc_dataset import DocDataset
import os
from typing import Dict, Union
import json
import pandas as pd
from tqdm import tqdm
import re
import importlib

class Agent:
    def __init__(self, config, model=None, **kwargs):
        self.config = config
        self.messages = None # store history
        if model is not None:
            self.model:BaseModel = model
        else:
            module = importlib.import_module(self.config.model.module_name)
            model_class = getattr(module, self.config.model.class_name)
            print("Create model: ", self.config.model.model_id)
            self.model = model_class(self.config.model)
    
    def clean_messages(self):
        """
        Reset history messages of this agent
        """
        self.messages = None
        
    def _predict(self, question, texts=None, images=None, add_to_message = False):
        if not self.config.agent.use_text:
            texts = None
        if not self.config.agent.use_image:
            images = None
        generated_ans, messages = self.model.predict(question, texts, images, self.messages)
        if add_to_message:
            self.messages = messages
        return generated_ans, messages
    
    def predict(self, question, texts=None, images=None, with_sys_prompt=True):
        """
        Predict the answer for the given question, by default, the system prompt will be added to the question, and the message history will be saved.
        """
        if with_sys_prompt:
            question = self.config.agent.system_prompt + question
        return self._predict(question, texts, images, add_to_message = True)
    
    def discuss(self, discussion_log, agent_idx, agent_ids):
        """
        Discuss with other agents, the discussion log is a dictionary with agent_id as key and the discussion content as value. The message history won't be saved.
        """
        prompt = f"{discussion_log}\n" + self.config.agent.discuss_prompt
        response_dict = {}
        for attempt in range(self.config.agent.max_retries):
            try:
                raw_response, _ = self._predict(question=prompt)
                match = re.search(r'\{.*?\}', raw_response)
                if match:
                    json_string = match.group(0)
                    response_dict = json.loads(json_string)
                break
            except json.JSONDecodeError:
                print(f"Attempt {attempt + 1} failed: Failed to decode response: {raw_response}")
            except Exception as e:
                print(f"Attempt {attempt + 1} failed with error: {str(e)}")
        
        turn_discussion = {agent_id: response_dict.get(str(agent_id), None) for agent_id in agent_ids}
        turn_discussion[agent_idx] = None
        
        return turn_discussion
    
    def self_reflect(self, prompt=None, add_to_message = True):
        """
        Self-reflect the history message of this agent. The result will also be added to history message by default.
        """
        if prompt is None:
            self_reflect_prompt = self.config.agent.self_reflect_prompt
        else:
            self_reflect_prompt = prompt
        
        generated_ans, messages = self._predict(question = self_reflect_prompt)
        if add_to_message:
            self.messages = messages
        
        return generated_ans
    
    def eval(self, question, answer, gt):
        """
        Evaluate the answer based on the ground truth. The evaluation result includes relevance, correctness, and binary_correctness.
        """
        prompt = self.config.agent.eval_system_prompt.format(question=question, answer=answer, gt=gt)
        try:
            generated_ans, _ = self.model.predict(prompt)
            result = extract_evaluation_metrics(generated_ans)
            return result
        except Exception as e:
            print(f"Error evaluating answer: {str(e)}")
            return {"relevance": 0, "correctness": 0, "binary_correctness": 0}
    
    def eval_dataset(self, dataset: DocDataset):
        """
        Evaluate the dataset using the model. The evaluation results will be saved to the result file.(You can custom your own dataset class and the corresponding eval_dataset method)
        """
        samples, ans_path = dataset.load_latest_results()
        if self.config.truncate_len:
            samples = samples[:self.config.truncate_len]
        
        samples_with_answer = []
        for sample in tqdm(samples):
            try:
                question = sample[dataset.config.question_key]
                answer = sample[self.config.ans_key]
                gt = sample[dataset.config.gt_key]
                result = self.eval(question, answer, gt)
                sample['relevance'] = result['relevance']
                sample['correctness'] = result['correctness']
                sample['binary_correctness'] = result.get('binary_correctness', None)
                samples_with_answer.append(sample)
            except Exception as e:
                print(f"Error evaluating sample: {str(e)}")
                
        ans_file_path_name = ans_path[:-5]+"_results.json"
        with open(ans_file_path_name, "w") as file:
            json.dump(samples_with_answer, file, indent=4)
            
        samples_with_answer = pd.DataFrame(samples_with_answer)
        path = os.path.join(dataset.config.result_dir,"results.txt")
        with open(path, "a") as file:
            file.write("\nEvaluation Results Summary:\n")
            file.write(f"Result file: {ans_path}\n")
            file.write(f"Average Relevance: {samples_with_answer['relevance'].mean():.3f}\n")
            file.write(f"Average Correctness: {samples_with_answer['correctness'].mean():.3f}\n")
            file.write(f"Average Binary Correctness: {samples_with_answer['binary_correctness'].mean():.3f}\n")
            samples_with_answer['binary_correctness_average'] = samples_with_answer['correctness'].apply(lambda x: 1 if x > 0.5 else 0)
            file.write(f"Average Binary Correctness (based on Average Correctness): {samples_with_answer['binary_correctness_average'].mean():.3f}\n")
        
        print(f"Save results to {path}.")

def extract_evaluation_metrics(eval_str: str) -> Dict[str, Union[float, int]]:
    try:
        start_index = eval_str.find('{') 
        end_index = eval_str.rfind('}') + 1 
        eval_str = eval_str[start_index:end_index]
        metrics = json.loads(eval_str)
        return {
            'relevance': float(metrics.get('relevance', 0.0)),
            'correctness': float(metrics.get('correctness', 0.0)),
            'binary_correctness': int(metrics.get('binary_correctness', 0))
        }
    except json.JSONDecodeError as e:
        return {
            'relevance': 0.0,
            'correctness': 0.0,
            'binary_correctness': 0
        }
    except Exception as e:
        return {
            'relevance': 0.0,
            'correctness': 0.0,
            'binary_correctness': 0
        }