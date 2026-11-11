"""Versioned AHAT rubric with adjacency, thermal-processing and meal policy."""
from pathlib import Path


PROMPT_VERSION = 'ahat-rubric-portions-and-order-v6'
PROMPT_DIR = Path(__file__).parent / 'paper_rubric'
NAMES = {
    'D1': 'Goal_Achievement',
    'D2': 'Intent_Understanding',
    'D3': 'Completeness',
    'D4': 'Execution_Quality',
}
PROMPTS = {key: (PROMPT_DIR / (name + '.txt')).read_text(encoding='utf-8') for key, name in NAMES.items()}
