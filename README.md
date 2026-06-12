# MedSchema

Canonical repository: https://github.com/hy1940562929-a11y/MedSchema

MedSchema is a Chinese medical schema-rule resource for neuro-symbolic reasoning. It contains 2,957 Datalog-style schema rules extracted from clinical guideline documents and released in two complementary formats:

- `MedSchema_knowledge_graph.jsonld`: JSON-LD for Semantic Web and knowledge-graph reasoning workflows.
- `finetune_dataset.jsonl`: JSONL instruction data for supervised fine-tuning of schema-rule extraction models.

The resource is designed for document-level extraction of nonlinearly composed medical logic, including conjunctions, explicit negation, multi-premise rule bodies, and variable cross-binding.

## Repository Contents

| Path | Description |
| --- | --- |
| `aligned_rules_zh.json` | Canonical aligned AST rule dataset. |
| `MedSchema_knowledge_graph.jsonld` | JSON-LD release for graph and symbolic reasoning. |
| `finetune_dataset.jsonl` | Instruction-tuning data generated from aligned rules. |
| `MedSchema_ZH_train_RAW.jsonl` | Raw instruction-style training data. |
| `GLOBAL_ONTOLOGY.json` | Global entity synonym and concept-normalization dictionary. |
| `input_pdfs/` | Source Chinese clinical guideline PDF files used by the pipeline. |
| `output_rules/` | Intermediate textual schema-rule extraction outputs. |
| `output_json/` | Intermediate AST JSON outputs. |
| `output_ontology/` | Per-document ontology extraction outputs. |
| `step1.py` | Phase 1: extract textual schema rules from PDFs with constrained LLM prompting. |
| `step2.py` | Phase 2: convert textual rules into AST JSON. |
| `step2.5.py` | Clean source text and spacing artifacts from PDF extraction. |
| `step3.py` | Extract local medical synonym dictionaries. |
| `step4.py` | Build the global ontology and align rule arguments. |
| `step6.py` | Convert rule data into instruction-tuning JSONL. |
| `step7.py` | Convert aligned AST rules into JSON-LD. |
| `LD.py` | Lightweight Datalog-style reasoning and safety-constraint verification example. |
| `check.py` | Evaluation script for schema-rule extraction experiments. |
| `docs/` | Format, pipeline, and reuse documentation. |

## Installation

Python 3.10 or later is recommended.

```bash
git clone https://github.com/hy1940562929-a11y/MedSchema.git
cd MedSchema
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## API Configuration

Some pipeline and evaluation scripts call OpenAI-compatible LLM endpoints. Configure credentials through environment variables instead of editing source files:

```bash
export DEEPSEEK_API_KEY="your_deepseek_api_key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"

# Optional local OpenAI-compatible model endpoint for check.py
export LOCAL_API_KEY="not-needed"
export LOCAL_BASE_URL="http://localhost:1234/v1"
export LOCAL_MODEL_NAME="qwen3.6-35b-a3b"
```

The released dataset files can be inspected and reused without any API key. API keys are only required when rerunning LLM-based extraction or evaluation scripts.

## Quick Start

Inspect the canonical AST dataset:

```bash
python count.py
```

Run the lightweight JSON-LD reasoning example:

```bash
python LD.py
```

Regenerate the JSON-LD release from the aligned AST rules:

```bash
python step7.py
```

## Pipeline Overview

The construction pipeline follows a two-stage human-machine workflow:

1. `step1.py`: segment clinical guideline PDFs and extract candidate schema rules under strict prompt constraints.
2. `step2.py`: parse candidate textual rules into AST-style JSON with explicit `head`, `body`, `variables`, and `source_text` fields.
3. `step2.5.py`: clean spacing and PDF extraction artifacts.
4. `step3.py`: extract local synonym dictionaries from source text.
5. `step4.py`: merge local dictionaries into `GLOBAL_ONTOLOGY.json` and align entities to concept identifiers.
6. `step6.py`: export JSONL instruction-tuning data.
7. `step7.py`: export JSON-LD for Semantic Web and symbolic reasoning use.

See `docs/PIPELINE.md` for the full pipeline description and expected inputs/outputs.

## Data Formats

Each aligned schema rule has the following AST-level structure:

```json
{
  "rule_name": "rule label",
  "head": {
    "is_negative": false,
    "name": "predicate name",
    "arguments": ["X", "Y"]
  },
  "body": [
    {
      "is_negative": false,
      "name": "condition predicate",
      "arguments": ["X"]
    }
  ],
  "variables": {
    "X": "patient"
  },
  "source_text": "source clinical guideline paragraph"
}
```

See `docs/FORMATS.md` for JSON, JSONL, and JSON-LD details.

## Reuse Notes

- Use `aligned_rules_zh.json` when you need the canonical AST rule data.
- Use `MedSchema_knowledge_graph.jsonld` when importing rules into graph or symbolic reasoning workflows.
- Use `finetune_dataset.jsonl` when training or evaluating LLM-based schema-rule extractors.
- To adapt the pipeline to another language or domain, replace `input_pdfs/` and rerun the extraction, parsing, ontology alignment, and export steps.

The dataset is a research resource and is not intended for direct clinical decision-making without independent medical validation.

## Archival Access

This repository includes `.zenodo.json` metadata to support a permanent Zenodo archival release. The Zenodo DOI will be added here after the archival record is created.

## License

Source code is released under the MIT License. Dataset and documentation files are released under the Creative Commons Attribution 4.0 International License (CC BY 4.0). See `LICENSE` and `DATA_LICENSE`.

## Citation

If you use MedSchema, please cite the ISWC 2026 paper:

```bibtex
@inproceedings{huang2026medschema,
  title = {MedSchema: A Chinese Medical Schema Rule Dataset for Advancing Neuro-Symbolic Reasoning},
  author = {Huang, Yu and Xiong, Ke and Xu, Chuanhao and Jiang, Tingxin and Liu, Yang and Zhang, Xiaowang},
  booktitle = {Proceedings of the International Semantic Web Conference},
  year = {2026}
}
```
