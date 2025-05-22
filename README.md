# EduVisAgent: A Multi-Agent Framework for Pedagogical Visualization

## Overview

This project implements a multi-agent system designed to generate comprehensive educational content based on user queries. It leverages a series of specialized language model (LM) agents working collaboratively to create detailed teaching plans, improve them through iterative feedback, and build structured content for various presentation formats. The core of the system is the `TeachAgentsIntermediateSystem`, which coordinates the entire workflow.

![Main System Architecture](./image/main.png)

## Requirements

1. **Python 3.12**
2. **OpenAI API Key**
3. **Conda** (recommended for environment management)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/aiming-lab/EduVisAgent
   cd EduVisAgent
   ```

2. **Create and activate Conda environment:**
   ```bash
   conda create -n eduvis python=3.12
   conda activate eduvis
   ```

3. **Install dependencies:**
   ```bash
   bash install.sh
   ```

4. **Set up environment variables:**
   Export your OpenAI API key as an environment variable in your terminal session. 
   ```bash
   export OPENAI_API_KEY="your_openai_api_key_here"
   ```


## Usage

### Basic Operation

Execute the main script to run the educational content generation system:

```bash
python scripts/run_teach_intermediate.py --question "Your educational question here"
```

By default, if no `--question` argument is provided, the script uses a predefined example query. 

Output will be saved in the `outputs/teach_intermediate/` directory, with subdirectory names containing a timestamp and a brief description of the query (e.g., `outputs/teach_intermediate/YYYYMMDD_HHMMSS_explain_concept_photosynthesis/`).

### Batch Processing of Educational Questions

For processing multiple educational questions from a dataset (e.g., `train.jsonl`), you can use the `run_teach_intermediate_batch.py` script. This script iterates through questions in a JSONL file and runs the full `TeachAgentsIntermediateSystem` for each.

```bash
python scripts/run_teach_intermediate_batch.py --data_file mydatasets/train.jsonl --limit 5
```

This script supports the following parameters:

-   `--data_file` (required): Path to the JSONL data file containing the questions (e.g., `mydatasets/train.jsonl`). Each JSON object in the file should have a `"question"` field.
-   `--limit` (optional): Number of questions to process from the beginning of the file. If not specified, all questions will be processed.

Output for each question will be saved in a separate subdirectory within `outputs/teach_intermediate_batch/`. Each subdirectory will be uniquely named using the line number from the input file, a timestamp, and a slug derived from the question.


## Directory Structure

```
EduVisAgent/
├── agents/                         # Core agent logic
├── config/                         # Configuration files
├── models/                         # Language model interfaces
├── mydatasets/                     # Dataset files
├── outputs/                        # Generated outputs
├── scripts/                        # Executable scripts
├── image/                          # Image resources
├── utils/                          # Utility functions and classes
└── README.md                       # This file
