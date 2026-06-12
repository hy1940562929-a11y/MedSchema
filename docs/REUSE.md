# Reuse Guide

This guide summarizes common reuse scenarios.

## Scenario 1: Inspect the Dataset

```bash
python count.py
```

This reports the number of schema rules, predicates, entities, negated rules, and predicate arity distribution in `aligned_rules_zh.json`.

## Scenario 2: Use Rules in a Symbolic Verifier

Start from `MedSchema_knowledge_graph.jsonld` or `aligned_rules_zh.json`.

The minimal reasoning loop is:

1. Load rules.
2. Create an A-Box of patient facts.
3. Match all body predicates against facts.
4. Treat `is_negative=true` predicates as explicit blocking conditions under the chosen closed-world or application-specific assumption.
5. Emit the rule head when all premises are satisfied.

`LD.py` provides a compact example of this process.

## Scenario 3: Train a Schema-Rule Extractor

Use `finetune_dataset.jsonl` as supervised instruction data. The target output follows the same schema-rule constraints used during dataset construction:

- maximum predicate arity of 3;
- no predicate nesting;
- no disjunction in rule bodies;
- explicit negation for exclusion conditions;
- variable binding across head and body predicates.

## Scenario 4: Adapt to a New Corpus

To build a related dataset:

1. Replace `input_pdfs/` with the new corpus.
2. Update the extraction prompt in `step1.py` if the target language, writing style, or domain differs.
3. Run the pipeline in order: `step1.py`, `step2.py`, `step2.5.py`, `step3.py`, `step4.py`, `step6.py`, `step7.py`.
4. Manually review a gold-standard subset to quantify structural and semantic quality.
5. Publish the resulting aligned AST, JSON-LD, JSONL, documentation, and license.

## Clinical Use Disclaimer

MedSchema is a research dataset. It should not be used for direct diagnosis, prescription, or clinical decision-making without independent clinical validation, local governance review, and expert oversight.
