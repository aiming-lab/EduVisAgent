import os
import re
import yaml
from types import SimpleNamespace # To convert dicts to objects for config

# Attempt to import BaseAgent. The exact path might need adjustment
# depending on your project structure and how BaseAgent is exposed.
# Assuming BaseAgent is in a file like 'base_agent.py' directly under the 'agents' directory
# or made available through the project's Python path.
try:
    from .base_agent import Agent as BaseAgent # If BaseAgent is named Agent in base_agent.py
except ImportError:
    # Fallback if the above relative import doesn't work (e.g. running script from project root)
    # This depends on sys.path being correctly set by the calling script
    from base_agent import Agent as BaseAgent


class TeachAgentsIntermediateSystem:
    def __init__(self, agent_config_dir: str, model_config_dir: str, agent_names_and_configs: dict, base_run_output_dir: str):
        self.agent_config_dir = agent_config_dir
        self.model_config_dir = model_config_dir
        self.agent_configs_map = agent_names_and_configs
        self.agents = {}
        self.base_run_output_dir = base_run_output_dir # New: For saving outputs
        self._ensure_dir(self.base_run_output_dir) # Ensure the base output dir exists
        self._load_agents()

    def _ensure_dir(self, directory_path):
        """Ensures that a directory exists, creating it if necessary."""
        os.makedirs(directory_path, exist_ok=True)

    def _save_text_to_file(self, filepath, content):
        """Saves text content to a file."""
        # Create parent directory if it doesn't exist
        self._ensure_dir(os.path.dirname(filepath))
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    def _load_agents(self):
        """Loads all necessary agents based on their configuration files."""
        print("Loading agents...")
        for agent_key, config_file_name in self.agent_configs_map.items():
            agent_config_path = os.path.join(self.agent_config_dir, config_file_name)
            
            # Load agent-specific config data (contains system_prompt, agent_name, model (string), etc.)
            with open(agent_config_path, 'r') as f:
                agent_specific_cfg_data = yaml.safe_load(f)

            # Get the model config name string (e.g., 'gpt4o_openai') and remove it from agent_specific_cfg_data,
            # as we don't want the 'model' string inside the 'agent' namespace.
            model_config_name_str = agent_specific_cfg_data.pop('model', None)
            if not model_config_name_str:
                raise ValueError(f"Agent config {config_file_name} must specify a 'model' string.")
            
            # Load the actual model configuration details (module_name, class_name, model_id, etc.)
            model_config_file_name = f"{model_config_name_str}.yaml"
            model_config_path = os.path.join(self.model_config_dir, model_config_file_name)
            with open(model_config_path, 'r') as f:
                actual_model_config_dict = yaml.safe_load(f)
            
            # Construct the final config object for BaseAgent
            # It should have a self.config.agent namespace and a self.config.model namespace
            config_for_base_agent = SimpleNamespace()
            config_for_base_agent.agent = SimpleNamespace(**agent_specific_cfg_data) # agent_name, system_prompt, etc.
            config_for_base_agent.model = SimpleNamespace(**actual_model_config_dict) # module_name, class_name, model_id, etc.
            
            try:
                # Pass the correctly structured config to BaseAgent
                self.agents[agent_key] = BaseAgent(config=config_for_base_agent) 
                print(f"Successfully loaded agent: {agent_key} ({config_file_name}) with model {model_config_name_str}")
            except Exception as e:
                print(f"Error instantiating agent {agent_key} with config {config_file_name}: {e}")
                import traceback
                traceback.print_exc()
                raise
        print("All agents loaded.")

    def _extract_parts_from_plan(self, plan_text: str) -> list[str]:
        """
        Extracts distinct parts from the initial teaching plan.
        Parts are expected to be enclosed in <PART N: TITLE>...</PART N: TITLE> tags.
        """
        # Previous regex: r"<PART \d+:.*?>(.*?)</PART \d+>"
        # New regex to match start and end tags with titles, using a backreference \1
        # to ensure the "N: TITLE" part is identical in both start and end tags.
        # Group 1 captures "N: TITLE", Group 2 captures the content.
        matches = re.findall(r"<PART (\d+:[^>]+)>(.*?)</PART \1>", plan_text, re.DOTALL)
        
        cleaned_parts = []
        # 'matches' is a list of tuples: (full_title_info, content_text)
        for _full_title_info, part_content in matches: # We only need the content for now
            content = part_content.strip()
            
            # The existing "---" cleaning logic can remain as a safeguard,
            # though it's less likely to be needed if the regex is precise.
            content_lines = content.splitlines()
            if content_lines and content_lines[0].strip() == "---":
                content_lines.pop(0)
            if content_lines and content_lines[-1].strip() == "---":
                content_lines.pop(-1)
            cleaned_parts.append("\n".join(content_lines).strip())
            
        if not cleaned_parts:
            print("Warning: No parts extracted from the plan using the new regex. "
                  "Check plan structure (e.g., <PART N: TITLE>...</PART N: TITLE> tags) and regex accuracy.")
            # Consider alternative regex or fallback if plan structure varies significantly.
            # For now, an empty list means subsequent steps might not have content to work with.
        return cleaned_parts

    def predict(self, user_query: str):
        """
        Orchestrates the TeachAgents intermediate workflow.
        """
        print(f"\n[System] Received query: {user_query[:100]}...")
        self._save_text_to_file(os.path.join(self.base_run_output_dir, "00_user_query.txt"), user_query)

        results = {
            "user_query": user_query,
            "initial_plan_combined_raw": None,
            "initial_parts_extracted": [],
            "refinement_details_per_part": [], # Will store dicts with feedback and refined content
            "final_refined_plan_combined": None,
            "final_refined_parts_separated": [],
            "ui_plans_for_each_part": []
        }

        # Phase 1: Generate Initial Plan
        print("\n[Phase 1] Generating initial teaching plan...")
        scenario_agent = self.agents['scenario_introducer']
        problem_solver_agent = self.agents['problem_solver']
        prompt1 = f"Based on the user's query: '{user_query}', generate an initial teaching scenario introduction and problem understanding. Frame this as the first part of a multi-part teaching plan. Ensure your output is enclosed in <PART 1: SCENARIO INTRODUCTION AND PROBLEM UNDERSTANDING>...</PART 1: SCENARIO INTRODUCTION AND PROBLEM UNDERSTANDING> tags."
        output_agent1, _ = scenario_agent.predict(prompt1)
        prompt2 = f"Given the scenario and problem understanding: '{output_agent1}', and the original query: '{user_query}', expand this into a comprehensive, multi-part (suggest aiming for 6 distinct parts including the first) initial teaching plan. Each part should address a different aspect (e.g., step-by-step, near transfer, far transfer, common mistakes, summary, metacognition). Enclose each part in <PART N: TITLE>...</PART N: TITLE> tags, ensuring the title is descriptive. The previous content from Part 1 should be integrated and potentially re-tagged if its title changes."
        combined_initial_plan, _ = problem_solver_agent.predict(prompt2)
        results["initial_plan_combined_raw"] = combined_initial_plan
        self._save_text_to_file(os.path.join(self.base_run_output_dir, "01_initial_plan_raw.txt"), combined_initial_plan)

        # Phase 2: Extract Parts
        print("\n[Phase 2] Extracting parts from initial plan...")
        initial_parts = self._extract_parts_from_plan(combined_initial_plan)
        results["initial_parts_extracted"] = initial_parts
        initial_parts_dir = os.path.join(self.base_run_output_dir, "02_initial_parts_extracted")
        self._ensure_dir(initial_parts_dir)
        for i, part_content in enumerate(initial_parts):
            self._save_text_to_file(os.path.join(initial_parts_dir, f"part_{i+1}.txt"), part_content)
        
        if not initial_parts:
            print("Error: No parts extracted from initial plan. Aborting further processing.")
            return results # Return partially filled results
        
        num_parts = len(initial_parts)
        print(f"Successfully extracted {num_parts} parts.")

        # Phase 3: Refine each part with discussion agents and a synthesizer
        print("\n[Phase 3] Refining each part...")
        refined_parts_content_list = []
        discussion_agent_keys = ['visual_representer', 'info_expresser', 'cognitive_strategist', 'meta_strategist']
        synthesizer_agent = self.agents['schema_instructor']
        refinement_base_dir = os.path.join(self.base_run_output_dir, "03_refinement_process")
        self._ensure_dir(refinement_base_dir)

        for i, part_content in enumerate(initial_parts):
            print(f"  Refining Part {i+1}/{num_parts}...")
            part_refinement_dir = os.path.join(refinement_base_dir, f"part_{i+1}")
            self._ensure_dir(part_refinement_dir)
            self._save_text_to_file(os.path.join(part_refinement_dir, "01_original_content.txt"), part_content)
            
            part_refinement_details = {"original_content": part_content, "feedbacks": {}, "combined_feedback": "", "refined_content": ""}
            
            feedbacks = []
            for agent_key_idx, agent_key in enumerate(discussion_agent_keys):
                discussion_agent = self.agents[agent_key]
                feedback_prompt = f"Consider the following segment of a teaching plan (Part {i+1}):\n\n'''\n{part_content}\n'''\n\nBased on your role as {discussion_agent.config.agent.agent_name}, provide specific suggestions, critiques, or enhancements for this segment. Focus on how it can be improved according to your specialization. If no improvements are needed, state that. Your feedback will be used to refine this part."
                print(f"    Getting feedback from {agent_key} for Part {i+1}...")
                feedback, _ = discussion_agent.predict(feedback_prompt)
                feedbacks.append(feedback)
                part_refinement_details["feedbacks"][agent_key] = feedback
                self._save_text_to_file(os.path.join(part_refinement_dir, f"{agent_key_idx+2:02d}_feedback_{agent_key}.txt"), feedback)
            
            combined_feedback_for_synthesizer = "\n\n---\n\n".join(feedbacks)
            part_refinement_details["combined_feedback"] = combined_feedback_for_synthesizer
            self._save_text_to_file(os.path.join(part_refinement_dir, f"{len(discussion_agent_keys)+2:02d}_combined_feedback_for_synthesizer.txt"), combined_feedback_for_synthesizer)

            synthesizer_prompt = f"You are a teaching plan synthesizer. Your task is to refine a segment of a teaching plan based on expert feedback. \nOriginal Plan Segment (Part {i+1}):\n'''\n{part_content}\n'''\n\nExpert Feedback from various specialists:\n'''\n{combined_feedback_for_synthesizer}\n'''\n\nBased on all the feedback, revise and rewrite the original plan segment to incorporate the suggestions and create an improved, coherent, and effective teaching segment. Output only the refined plan segment for Part {i+1}."
            print(f"    Synthesizing refined Part {i+1} using {synthesizer_agent.config.agent.agent_name}...")
            refined_part_content, _ = synthesizer_agent.predict(synthesizer_prompt)
            refined_parts_content_list.append(refined_part_content)
            part_refinement_details["refined_content"] = refined_part_content
            results["refinement_details_per_part"].append(part_refinement_details)
            self._save_text_to_file(os.path.join(part_refinement_dir, f"{len(discussion_agent_keys)+3:02d}_refined_content_by_{synthesizer_agent.config.agent.agent_name.replace(' ', '_').lower()}.txt"), refined_part_content)

        results["final_refined_parts_separated"] = refined_parts_content_list
        final_refined_parts_separated_dir = os.path.join(self.base_run_output_dir, "05_final_refined_parts_separated")
        self._ensure_dir(final_refined_parts_separated_dir)
        for i, content in enumerate(refined_parts_content_list):
            self._save_text_to_file(os.path.join(final_refined_parts_separated_dir, f"part_{i+1}.txt"), content)

        results["final_refined_plan_combined"] = "\n\n---\n\n".join(refined_parts_content_list)
        self._save_text_to_file(os.path.join(self.base_run_output_dir, "04_final_refined_plan_combined.txt"), results["final_refined_plan_combined"])

        # Phase 4: Generate UI Plan for each refined part
        print("\n[Phase 4] Generating UI plans for each refined part...")
        ui_planner_agent = self.agents['ui_planner']
        ui_plans_list = []
        ui_plans_dir = os.path.join(self.base_run_output_dir, "06_ui_plans_for_each_part")
        self._ensure_dir(ui_plans_dir)

        for i, refined_part_text in enumerate(refined_parts_content_list):
            ui_planning_prompt = f"Given the following refined teaching plan segment (Part {i+1}):\n'''\n{refined_part_text}\n'''\nGenerate a UI plan for presenting this segment on a webpage using Shadcn/UI components. Structure your plan with headings: 1. Overall Layout Idea, 2. Key Shadcn/UI Components, 3. Content Mapping, 4. Interactivity (if applicable), 5. Mathematical Notation (if applicable). Be specific about component usage and content placement."
            print(f"  Generating UI plan for Part {i+1}...")
            ui_plan, _ = ui_planner_agent.predict(ui_planning_prompt)
            ui_plans_list.append(ui_plan)
            self._save_text_to_file(os.path.join(ui_plans_dir, f"ui_plan_part_{i+1}.txt"), ui_plan)
        
        results["ui_plans_for_each_part"] = ui_plans_list

        print("\nTeachAgents Intermediate System processing complete.")
        print(f"All intermediate and final outputs saved in: {self.base_run_output_dir}")
        return results
