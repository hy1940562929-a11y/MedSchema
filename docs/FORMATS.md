# Data Formats

MedSchema is released in three main machine-readable formats.

## AST JSON

File: `aligned_rules_zh.json`

This is the canonical aligned rule dataset. It is a JSON array where each item is one schema rule.

```json
{
  "rule_name": "怀疑IAI患者的诊断性腹腔穿刺应用与感染程度判断",
  "head": {
    "is_negative": false,
    "name": "进行检测",
    "arguments": ["X", "Y"]
  },
  "body": [
    {
      "is_negative": false,
      "name": "怀疑IAI病人",
      "arguments": ["X"]
    }
  ],
  "variables": {
    "X": "病人",
    "Y": "诊断性腹腔穿刺检测"
  },
  "source_text": "source guideline paragraph"
}
```

Fields:

- `rule_name`: human-readable rule label.
- `head`: conclusion predicate of the rule.
- `body`: list of premise predicates interpreted conjunctively.
- `is_negative`: whether the predicate is explicitly negated.
- `name`: predicate name.
- `arguments`: ordered predicate arguments. Variables such as `X`, `Y`, and `Z` bind entities across the rule.
- `variables`: variable-to-entity-type mapping.
- `source_text`: source paragraph from the clinical guideline.

## JSON-LD

File: `MedSchema_knowledge_graph.jsonld`

The JSON-LD export represents rules and predicates as graph nodes. It is intended for Semantic Web, knowledge-graph, and symbolic reasoning workflows.

Important context mappings:

- `Rule` maps to `medschema:SchemaRule`.
- `Predicate` maps to `medschema:LogicalPredicate`.
- `has_head` maps to `medschema:hasHead`.
- `has_body` maps to `medschema:hasBody`.
- `is_negative` maps to `medschema:isNegative`.
- `arguments` maps to an ordered JSON-LD list through `medschema:hasArgument`.

Typical uses:

- Import into graph tooling for inspection and linking.
- Convert predicate structures into Datalog-style rules.
- Run controlled reasoning experiments over rule bodies and patient facts.

## Instruction-Tuning JSONL

File: `finetune_dataset.jsonl`

Each line is a training example in chat-message format:

```json
{
  "messages": [
    {"role": "system", "content": "schema-rule extraction instructions"},
    {"role": "user", "content": "source clinical text"},
    {"role": "assistant", "content": "target schema rules"}
  ]
}
```

Typical uses:

- Supervised fine-tuning of LLM-based schema-rule extractors.
- Evaluation of strict rule extraction under controlled prompts.
- Benchmarking document-level nonlinear medical logic extraction.

## Choosing a Format

Use `aligned_rules_zh.json` for direct programmatic access to the canonical rules.

Use `MedSchema_knowledge_graph.jsonld` for graph integration, Semantic Web workflows, or symbolic reasoning.

Use `finetune_dataset.jsonl` for neural model training and evaluation.
