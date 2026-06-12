# MedSchema Pipeline Guide

This document describes how to reuse the MedSchema construction pipeline.

## Inputs

Place source clinical guideline PDFs in:

```text
input_pdfs/
```

The current repository includes the Chinese clinical guideline PDFs used for the released MedSchema resource.

## Environment

Install dependencies:

```bash
pip install -r requirements.txt
```

Set an OpenAI-compatible API key for scripts that call an LLM:

```bash
export DEEPSEEK_API_KEY="your_deepseek_api_key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
```

## Step-by-Step Workflow

### Step 1: Constrained Rule Extraction

```bash
python step1.py
```

Input: `input_pdfs/`

Output: `output_rules/*.txt`

This step segments guideline PDFs and extracts candidate textual schema rules with constrained prompting. It enforces arity limits, no nested predicates, no disjunction in rule bodies, and explicit negation for exclusion criteria.

### Step 2: AST Parsing

```bash
python step2.py
```

Input: `output_rules/*.txt`

Output: `output_json/*.json`

This step converts textual schema rules into structured AST JSON objects with `head`, `body`, `variables`, and `source_text`.

### Step 2.5: Source Text Cleaning

```bash
python step2.5.py
```

Input: `output_json/*.json`

Output: `output_json_cleaned/*.json`

This step removes PDF extraction spacing artifacts while preserving the rule structure.

### Step 3: Local Ontology Extraction

```bash
python step3.py
```

Input: source text from extracted rules

Output: `output_ontology/*.json`

This step extracts document-level synonym dictionaries for medical concepts.

### Step 4: Global Ontology Alignment

```bash
python step4.py
```

Inputs: `output_json_cleaned/`, `output_ontology/`

Outputs: `GLOBAL_ONTOLOGY.json`, `aligned_rules_zh.json`

This step merges local synonym dictionaries and normalizes rule arguments to global concept identifiers where possible.

### Step 6: Instruction-Tuning Export

```bash
python step6.py
```

Input: aligned rule data

Output: `finetune_dataset.jsonl`

This step creates JSONL instruction data for supervised fine-tuning.

### Step 7: JSON-LD Export

```bash
python step7.py
```

Input: `aligned_rules_zh.json`

Output: `MedSchema_knowledge_graph.jsonld`

This step serializes schema rules into JSON-LD with a compact `@context`, rule nodes, predicate nodes, ordered arguments, and explicit negation attributes.

## Verification

Run the lightweight reasoning example:

```bash
python LD.py
```

This script loads `MedSchema_knowledge_graph.jsonld`, creates virtual patient facts, and checks whether explicit negation blocks unsafe derivations in a controlled Datalog-style setting.

## Notes for Adapting the Pipeline

To reuse the pipeline for another corpus:

1. Replace the files in `input_pdfs/`.
2. Update prompts if the target language or domain differs substantially.
3. Rerun Steps 1-4 to build aligned rules and a new ontology.
4. Rerun Steps 6-7 to export JSONL and JSON-LD.
5. Manually inspect a sample of generated rules before downstream use.

The pipeline is intended to accelerate expert curation. It should not be treated as a fully automated clinical validation system.
