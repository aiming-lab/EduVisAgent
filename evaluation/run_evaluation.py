#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import base64
import argparse
from openai import OpenAI, OpenAIError

# --- Configuration ---
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY in your environment.")
client = OpenAI(api_key=API_KEY)

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths are now relative to the script's directory
QUESTIONS_FILE_PATH = os.path.join(SCRIPT_DIR, "data.json")
ANSWERS_BASE_DIR = os.path.join(SCRIPT_DIR, "data")

BENCHMARK_GUIDELINES = """
    Category I: Visual Scenario Design Guidance
    Level 1: The image contains no scenes or illustrations, presenting only text and formulas with no contextual visual cues, failing to engage interest or connect mathematical concepts to real-world contexts.
    Level 2: The image includes a single static illustration or low-fidelity mockup with minimal labeling that does not highlight variables or key objects, offering limited context and poor immersion.
    Level 3: Multiple static schematic diagrams or sketch-style illustrations appear in the image, labeling core objects, variables, and simple steps, providing basic visual guidance but lacking layered coherence.
    Level 4: The image integrates scenario illustrations, storyboard panels, and infographics to present the process in multiple views and steps, with annotations and captions guiding students through mapping abstract concepts to context.
    Level 5: Storyboard-style illustrations and infographics are fused into a single image, including overview, detailed close-ups, and key pathway diagrams with comprehensive annotations, allowing students to grasp the entire flow and conceptual network at a glance.

    Category II: Visual Illustration Design
    Level 1: The image contains no charts, axes, or flow diagrams—only text. Without embedded visual tools, students cannot systematically organize or analyze quantities and relationships.
    Level 2: The image includes a single black-and-white bar chart or simple flow diagram, but scales and labels are incomplete, making variable relationships unclear and visual support minimal.
    Level 3: The image presents a static number line and colored bar chart with complete scales and legends, helping students grasp basic numerical changes visually, though comparison and context layering are absent.
    Level 4: The image combines number lines, flowcharts, infographics, and arrow annotations; multiple visuals are juxtaposed or overlaid to show processes and variable changes for a coherent modeling view.
    Level 5: The image presents a dashboard-style visualization integrating axes, bar charts, flow diagrams, heatmaps, etc., with linked elements that deeply visualize data relationships and model structure.

    Category III: Text–Illustration Coordination
    Level 1: Text and illustrations in the image are completely disconnected, with no labels, legends, or connectors—students cannot use visuals to understand text or formulas.
    Level 2: Text occasionally prompts “see diagram” or “refer to the illustration,” but the image lacks legends or clear labels, so mapping between text and graphics remains ambiguous.
    Level 3: Text descriptions and image elements share consistent numbering, color blocks, or arrows linked to a simple legend, explaining core symbols and variables to support initial mapping.
    Level 4: Text paragraphs are laid out alongside corresponding visuals within the same image, with detailed legends and color-coded annotations enabling simultaneous reading and mapping.
    Level 5: Text, formulas, and legends are fully integrated in one image, using consistent colors, numbering, and layered layout to achieve seamless text–graphic fusion for complete structural understanding.

    Category IV: Learning Thought Guidance
    Level 1: The image offers no visualized problem-solving guidance, showing only the problem statement and formulas, leaving students without strategic cues or reflection prompts.
    Level 2: The image embeds a simple flowchart or two title-style hints (e.g., “Identify problem type,” “Check result”), but the flowchart is overly simplistic and hints lack hierarchical detail.
    Level 3: The image displays a step-by-step flowchart template with key thinking nodes and self-check checkpoints, leaving annotation space for students to visually record their reasoning.
    Level 4: The image combines a near-transfer exercise with a comparative thought diagram, visually highlighting strategy differences so students can apply existing reasoning to a new context.
    Level 5: The image fuses near- and far-transfer exercises, concept mind maps, and a reflection panel into a dashboard-style layout, allowing students to review and extend their problem-solving network visually.

    Category V: Interactivity and Personalized Support
    Level 1: The image includes no feedback or support components—only a static problem statement and answer field—offering no hints, examples, or error cues and resulting in a nonresponsive visual.
    Level 2: The image shows fixed hint boxes (e.g., “Hint: draw a number line,” “Hint: check rounding”), but hints are not tailored to student responses, limiting personalized guidance.
    Level 3: The image integrates multiple static correction tips and example solution modules (common mistakes and standard approaches), which students can reference visually but without intelligent recommendations.
    Level 4: The image presents example solution workflows, text hints, and a common-errors analysis section highlighted with color blocks and arrows, providing diverse visual support in a single layout.
    Level 5: The image displays a comprehensive visual support panel with difficulty suggestions, personalized hints, worked examples, and extension resource links, enabling students to select tailored guidance directly from the visual layout.
"""

# --- Helper Functions ---
def encode_image_to_data_url(image_path):
    """Read an image file and return a data URL for embedding."""
    try:
        with open(image_path, "rb") as image_file:
            raw_bytes = image_file.read()
        b64_string = base64.b64encode(raw_bytes).decode("utf-8")
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
        return f"data:{mime_type};base64,{b64_string}"
    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"Error encoding image {image_path}: {e}")
        return None

def parse_gpt_response(response_content):
    """Extracts JSON from GPT's response string."""
    try:
        # Find the start and end of the JSON object
        start_index = response_content.find("{")
        end_index = response_content.rfind("}") + 1
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = response_content[start_index:end_index]
            return json.loads(json_str)
        else:
            print(f"Error: Could not find valid JSON in response: {response_content}")
            return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from response: {response_content}. Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while parsing GPT response: {e}")
        return None

# --- Evaluation Functions ---
def evaluate_image_q_single_a(question_image_path, answer_image_path):
    """Evaluates an image question against a single answer image."""
    q_url = encode_image_to_data_url(question_image_path)
    a_url = encode_image_to_data_url(answer_image_path)

    if not q_url or not a_url:
        return None, "Failed to encode one or both images."

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": BENCHMARK_GUIDELINES.strip()},
                {"type": "text", "text": "Problem image:"},
                {"type": "image_url", "image_url": {"url": q_url}},
                {"type": "text", "text": "Answer screenshot:"},
                {"type": "image_url", "image_url": {"url": a_url}},
                {"type": "text", "text": (
                    "Assign integer scores 0–5 for categories 1–5. "
                    "0 = completely missing or very poor; 5 = fully meets highest level. "
                    "Return ONLY a JSON object like {\"1\":0,\"2\":1,\"3\":2,\"4\":3,\"5\":4}."
                )}
            ]
        }
    ]
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1", 
            messages=messages,
            temperature=0.0,
            max_tokens=250
        )
        content = resp.choices[0].message.content.strip()
        scores = parse_gpt_response(content)
        return scores, None if scores else "Failed to parse scores from GPT response."
    except OpenAIError as e:
        return None, f"OpenAI API error: {e}"
    except Exception as e:
        return None, f"Unexpected error during API call: {e}"

def evaluate_image_q_multiple_a(question_image_path, answer_image_paths):
    """Evaluates an image question against multiple answer images."""
    q_url = encode_image_to_data_url(question_image_path)
    if not q_url:
        return None, "Failed to encode question image."

    content_parts = [
        {"type": "text", "text": BENCHMARK_GUIDELINES.strip()},
        {"type": "text", "text": "Problem image:"},
        {"type": "image_url", "image_url": {"url": q_url}},
        {"type": "text", "text": "Student visual responses (multiple answer images follow):"}
    ]

    for ans_path in answer_image_paths:
        ans_url = encode_image_to_data_url(ans_path)
        if ans_url:
            content_parts.append({"type": "image_url", "image_url": {"url": ans_url}})
        else:
            return None, f"Failed to encode an answer image: {ans_path}"
    
    content_parts.append({
        "type": "text",
        "text": (
            "Based on the problem image and all student visual responses above, assign integer scores 0–5 for categories 1–5. "
            "0 = completely missing or very poor; 5 = fully meets highest level. "
            "Return ONLY a JSON object like {\"1\":0,\"2\":1,\"3\":2,\"4\":3,\"5\":4}."
        )
    })

    messages = [{"role": "user", "content": content_parts}]
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.0,
            max_tokens=250
        )
        content = resp.choices[0].message.content.strip()
        scores = parse_gpt_response(content)
        return scores, None if scores else "Failed to parse scores from GPT response."
    except OpenAIError as e:
        return None, f"OpenAI API error: {e}"
    except Exception as e:
        return None, f"Unexpected error during API call: {e}"

def evaluate_text_q_single_a(question_text, answer_image_path):
    """Evaluates a text question against a single answer image using BENCHMARK_GUIDELINES."""
    a_url = encode_image_to_data_url(answer_image_path)
    if not a_url:
        return None, "Failed to encode answer image."

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": BENCHMARK_GUIDELINES.strip()},
                {"type": "text", "text": f"Question:\n{question_text}"},
                {"type": "text", "text": "Answer screenshot:"},
                {"type": "image_url", "image_url": {"url": a_url}},
                {"type": "text", "text": (
                    "Based on the question text and the answer screenshot, assign integer scores 0–5 for categories 1–5. "
                    "0 = completely missing or very poor; 5 = fully meets highest level. "
                    "Return ONLY a JSON object like {\"1\":0,\"2\":1,\"3\":2,\"4\":3,\"5\":4}."
                )}
            ]
        }
    ]
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.0,
            max_tokens=250
        )
        content = resp.choices[0].message.content.strip()
        scores = parse_gpt_response(content)
        return scores, None if scores else "Failed to parse scores from GPT response."
    except OpenAIError as e:
        return None, f"OpenAI API error: {e}"
    except Exception as e:
        return None, f"Unexpected error during API call: {e}"

def evaluate_text_q_multiple_a(question_text, answer_image_paths):
    """Evaluates a text question against multiple answer images using BENCHMARK_GUIDELINES."""
    content_parts = [
        {"type": "text", "text": BENCHMARK_GUIDELINES.strip()},
        {"type": "text", "text": f"Question:\n{question_text}"},
        {"type": "text", "text": "Student visual responses (multiple answer images follow):"}
    ]

    for ans_path in answer_image_paths:
        ans_url = encode_image_to_data_url(ans_path)
        if ans_url:
            content_parts.append({"type": "image_url", "image_url": {"url": ans_url}})
        else:
            return None, f"Failed to encode an answer image: {ans_path}"
    
    content_parts.append({
        "type": "text",
        "text": (
            "Based on the question text and all student visual responses above, assign integer scores 0–5 for categories 1–5. "
            "0 = completely missing or very poor; 5 = fully meets highest level. "
            "Return ONLY a JSON object like {\"1\":0,\"2\":1,\"3\":2,\"4\":3,\"5\":4}."
        )
    })

    messages = [{"role": "user", "content": content_parts}]
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            temperature=0.0,
            max_tokens=250
        )
        content = resp.choices[0].message.content.strip()
        scores = parse_gpt_response(content)
        return scores, None if scores else "Failed to parse scores from GPT response."
    except OpenAIError as e:
        return None, f"OpenAI API error: {e}"
    except Exception as e:
        return None, f"Unexpected error during API call: {e}"

# --- Main Logic --- 
def main():
    parser = argparse.ArgumentParser(description="Evaluate questions based on images using OpenAI API.")
    parser.add_argument("--questions_file", type=str, default=QUESTIONS_FILE_PATH,
                        help="Path to the JSON file containing questions.")
    parser.add_argument("--answers_dir", type=str, default=ANSWERS_BASE_DIR,
                        help="Base directory containing answer image folders named by question ID.")
    parser.add_argument("--output_file", type=str, default="evaluation.json",
                        help="Name of the output JSON file for results.")
    args = parser.parse_args()

    try:
        with open(args.questions_file, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Questions file not found at {args.questions_file}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {args.questions_file}")
        return

    all_results = []

    for question_item in questions_data:
        question_id = question_item.get("id")
        question_content = question_item.get("question")
        subject = question_item.get("subject", "N/A") # Optional subject

        if not question_id or not question_content:
            print(f"Skipping item due to missing 'id' or 'question': {question_item}")
            continue

        print(f"Processing Question ID: {question_id}...")

        result_entry = {
            "question_id": question_id,
            "subject": subject,
            "question_raw": question_content,
            "question_type": None,
            "question_path_or_text": None,
            "answer_image_paths": [],
            "num_answer_images": 0,
            "category_scores": None,
            "total_score": 0,
            "error_message": None
        }

        answer_folder_path = os.path.join(args.answers_dir, str(question_id))
        if not os.path.isdir(answer_folder_path):
            print(f"  Answer folder not found: {answer_folder_path}")
            result_entry["error_message"] = "Answer folder not found."
            all_results.append(result_entry)
            continue

        answer_image_files = sorted([
            os.path.join(answer_folder_path, f) 
            for f in os.listdir(answer_folder_path) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))
        ])
        result_entry["answer_image_paths"] = answer_image_files
        result_entry["num_answer_images"] = len(answer_image_files)

        if not answer_image_files:
            print(f"  No answer images found in {answer_folder_path}")
            result_entry["error_message"] = "No answer images found."
            all_results.append(result_entry)
            continue

        is_image_question = isinstance(question_content, str) and question_content.lower().endswith(('.png', '.jpg', '.jpeg'))

        if is_image_question:
            result_entry["question_type"] = "Image"
            full_question_image_path = os.path.join(SCRIPT_DIR, question_content)
            result_entry["question_path_or_text"] = full_question_image_path
            if not os.path.isfile(full_question_image_path):
                print(f"  Question image not found: {full_question_image_path}")
                result_entry["error_message"] = "Question image file not found."
                all_results.append(result_entry)
                continue
            
            if len(answer_image_files) == 1:
                print(f"  Type: Image Question, Single Answer Image. Evaluating...")
                scores, err = evaluate_image_q_single_a(full_question_image_path, answer_image_files[0])
            else:
                print(f"  Type: Image Question, Multiple Answer Images. Evaluating...")
                scores, err = evaluate_image_q_multiple_a(full_question_image_path, answer_image_files)
        else:
            result_entry["question_type"] = "Text"
            result_entry["question_path_or_text"] = question_content # It's the text itself
            if len(answer_image_files) == 1:
                print(f"  Type: Text Question, Single Answer Image. Evaluating...")
                scores, err = evaluate_text_q_single_a(question_content, answer_image_files[0])
            else:
                print(f"  Type: Text Question, Multiple Answer Images. Evaluating...")
                scores, err = evaluate_text_q_multiple_a(question_content, answer_image_files)

        if err:
            print(f"  Error during evaluation: {err}")
            result_entry["error_message"] = err
        elif scores:
            result_entry["category_scores"] = scores
            result_entry["total_score"] = sum(scores.values()) if isinstance(scores, dict) else 0
            print(f"  Scores: {scores}, Total: {result_entry['total_score']}")
        else:
            result_entry["error_message"] = "Evaluation completed but no scores were returned."

        all_results.append(result_entry)
        time.sleep(1) # Basic rate limiting

    # Save all results to the specified output file
    # Output file path will be relative to the script's directory if a relative path is given,
    # or an absolute path if an absolute path is given.
    if os.path.isabs(args.output_file):
        output_file_path = args.output_file
    else:
        output_file_path = os.path.join(SCRIPT_DIR, args.output_file)

    try:
        with open(output_file_path, 'w', encoding='utf-8') as f_out:
            json.dump(all_results, f_out, indent=4, ensure_ascii=False)
        print(f"\nResults saved to {output_file_path}")
    except IOError as e:
        print(f"\nError saving results to {output_file_path}: {e}")

if __name__ == "__main__":
    main()
