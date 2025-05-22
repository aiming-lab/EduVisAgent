import os
import sys
import yaml # For pretty printing results
import argparse
import datetime # For timestamped output folders
import re # For creating a safe slug from the query

# Adjust Python path to find the 'agents' and 'models' modules if necessary
# This assumes 'scripts' is a sibling to 'agents' and 'models' directories
# and the main project root is one level up from 'scripts.'
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from agents.teach_agents_intermediate_system import TeachAgentsIntermediateSystem

def ensure_dir(directory_path):
    """Ensures that a directory exists, creating it if necessary."""
    # This function is now primarily for the top-level outputs directory in this script
    os.makedirs(directory_path, exist_ok=True)

# Removed save_text_to_file as it's now in TeachAgentsIntermediateSystem

def create_query_slug(query, max_length=50):
    """Creates a file-system-safe slug from the user query."""
    slug = query.lower()
    slug = re.sub(r'\s+', '_', slug)
    slug = re.sub(r'[^\w_.-]', '', slug)
    return slug[:max_length]

def main():
    parser = argparse.ArgumentParser(description="Run TeachAgents Intermediate System.")
    parser.add_argument(
        "--question", 
        type=str, 
        default="Explain the concept of photosynthesis to a 5th grader, including what plants need and what they produce. Provide a simple real-world example.",
        help="The educational question to process."
    )
    args = parser.parse_args()

    # --- Create the base output directory for this specific run ---    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    query_slug = create_query_slug(args.question)
    run_folder_name = f"{timestamp}_{query_slug}"
    # Parent directory for all runs of this type
    teach_intermediate_outputs_dir = os.path.join(project_root, "outputs", "teach_intermediate")
    ensure_dir(teach_intermediate_outputs_dir) # Ensure the 'teach_intermediate' parent dir exists
    # Specific directory for this run's outputs
    base_run_output_dir_for_system = os.path.join(teach_intermediate_outputs_dir, run_folder_name)
    # The system itself will create this specific run_folder_name directory if passed, or use it if it exists.

    # Configuration for TeachAgentsIntermediateSystem
    agent_config_dir = os.path.join(project_root, "config", "agent")
    model_config_dir = os.path.join(project_root, "config", "model")
    agent_names_and_configs = {
        'scenario_introducer': 'teach_scenario_introduction_agent.yaml',
        'problem_solver': 'teach_problem_solving_agent.yaml',
        'schema_instructor': 'teach_schema_instruction_specialist.yaml',
        'visual_representer': 'teach_visual_representation_specialist.yaml',
        'info_expresser': 'teach_information_expression_specialist.yaml',
        'cognitive_strategist': 'teach_cognitive_strategy_agent.yaml',
        'meta_strategist': 'teach_metacognitive_strategy_agent.yaml',
        'ui_planner': 'teach_web_page_formatting_specialist.yaml'
    }

    print("Initializing TeachAgentsIntermediateSystem...")
    try:
        teach_system = TeachAgentsIntermediateSystem(
            agent_config_dir=agent_config_dir,
            model_config_dir=model_config_dir,
            agent_names_and_configs=agent_names_and_configs,
            base_run_output_dir=base_run_output_dir_for_system # Pass the run-specific output dir
        )
    except Exception as e:
        print(f"Error initializing TeachAgentsIntermediateSystem: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"\nProcessing question: {args.question[:100]}...")
    try:
        results = teach_system.predict(args.question)
    except Exception as e:
        print(f"Error during system prediction: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n--- Teach System Processing Finished ---")
    print(f"All intermediate and final outputs should be saved in: {base_run_output_dir_for_system}")
    
    # Optionally, still print a summary or a specific part of the results to console if desired
    if results:
        print("\n--- Final Combined Refined Plan (Preview from results dict) ---")
        print(results.get("final_refined_plan_combined", "Not available."))
    else:
        print("No results returned from the system.")

if __name__ == "__main__":
    main()
