import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agents.custom_method import Method2
import hydra

@hydra.main(config_path="../config", config_name="base", version_base="1.2")
def main(cfg):
    os.environ["CUDA_VISIBLE_DEVICES"] = cfg.multi_agents.cuda_visible_devices
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:64"
    for agent_config in cfg.multi_agents.agents:
        agent_name = agent_config.agent
        model_name = agent_config.model
        agent_cfg = hydra.compose(config_name="agent/"+agent_name, overrides=[]).agent
        model_cfg = hydra.compose(config_name="model/"+model_name, overrides=[]).model
        agent_config.agent = agent_cfg
        agent_config.model = model_cfg
    
    try:
        cfg.multi_agents.sum_agent.agent = hydra.compose(config_name="agent/"+cfg.multi_agents.sum_agent.agent, overrides=[]).agent
        cfg.multi_agents.sum_agent.model = hydra.compose(config_name="model/"+cfg.multi_agents.sum_agent.model, overrides=[]).model
    except:
        print("No sum agent")
        
    multi_agents = Method2(cfg.multi_agents)
    results, messages = multi_agents.predict("What is the capital of France?")
    print(results)
    print(messages)
    
if __name__ == "__main__":
    main()