# EduVisBench Dataset

## Overview

The EduVisBench dataset is a comprehensive collection of educational questions designed to benchmark and evaluate pedagogical visualizations. It is curated from a variety of high-quality sources, covering multiple subjects and difficulty levels to provide a robust testbed for educational content generation systems like EduVisAgent.

The dataset is structured to support the evaluation of generated visualizations across five key dimensions as outlined in our paper, "From EduVisBench to EduVisAgent: A Benchmark and Multi-Agent Framework for Pedagogical Visualization."

## Data Structure

The core of the dataset is `evaluation/data/data.json`, a JSON file containing a list of questions. Each question is represented as a JSON object with the following fields:

-   `subject` (string): The academic subject of the question (e.g., `chemistry`, `physics`, `maths`).
-   `data_source` (string): The original source of the question (e.g., `AI4Chem/C-MHChem-Benchmark-Chinese-Middle-high-school-Chemistry-Test`).
-   `id` (integer): A unique identifier for the question.
-   `difficulty` (string): The difficulty level of the question (e.g., `easy`, `medium`, `hard`, `difficult`). Some entries may use `Image` or `Text` to denote the format.
-   `question` (string): The full text of the question.

## Data Statistics

As of the latest analysis, the dataset contains **1154** questions with the following distribution:

### By Subject

-   **Maths:** 732 questions
-   **Chemistry:** 215 questions
-   **Physics:** 207 questions


### By Data Source

-   **illustrativemathematics:** 532 questions
-   **AI4Chem/C-MHChem-Benchmark-Chinese-Middle-high-school-Chemistry-Test:** 215 questions
-   **mrohith29/high-school-physics:** 207 questions
-   **HuggingFaceH4/MATH-500:** 200 questions

## Data Sources

The EduVisBench dataset is compiled from the following reputable sources to ensure a high standard of quality and relevance:

1.  **Illustrative Mathematics**
    -   A collection of high-quality, standards-aligned math problems that are rich in context and require deep conceptual understanding.

2.  **AI4Chem/C-MHChem-Benchmark-Chinese-Middle-high-school-Chemistry-Test**
    -   A benchmark dataset of middle and high school chemistry questions, providing a strong foundation for chemistry-related visualizations.

3.  **mrohith29/high-school-physics**
    -   A dataset of high school physics problems, covering a wide range of topics and concepts in classical mechanics, electricity, and magnetism.

4.  **HuggingFaceH4/MATH-500**
    -   A dataset of challenging math problems that require advanced reasoning and problem-solving skills.

This diverse collection of data ensures that EduVisAgent is tested on a wide spectrum of educational content, making the EduVisBench benchmark a reliable tool for evaluating pedagogical visualizations.
