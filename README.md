# Archon

**A multi-stage LLM pipeline that converts natural-language app descriptions into structured, machine-readable schemas.**

---

## Overview

Archon takes a plain-English description of an application (e.g. *"a to-do list app with tags and reminders"*) and runs it through a multi-stage LLM pipeline to produce a structured schema — entities, fields, relationships, and constraints — that downstream tools (code generators, form builders, database designers, etc.) can consume directly.

It was originally built as a take-home assignment for an AI Engineer role, and is maintained here as a standalone portfolio project.

## Why Archon?

Turning a fuzzy product idea into something a machine can act on usually means a human sitting down and manually writing out a data model. Archon automates that translation step — using an LLM not as a one-shot text generator, but as a multi-stage reasoning pipeline that checks and refines its own output before returning a final schema.

## How It Works

Archon breaks schema generation into discrete stages rather than asking a single prompt to do everything at once:

1. **Intent extraction** — parses the natural-language description to identify the core entities and actions implied by the app idea.
2. **Schema drafting** — generates an initial structured schema (entities, fields, types, relationships) from the extracted intent.
3. **Validation / refinement** — reviews the draft schema for consistency, missing fields, or ambiguous relationships, and revises it.
4. **Structured output** — emits the final schema in a clean, machine-readable format (JSON).

## Tech Stack

- **Language:** Python
- **Core:** LLM-based multi-stage pipeline


## Example

**Input:**
```
A habit tracker app where users can create habits, mark them done daily, and see a streak count.
```

**Output (illustrative):**
```json
{
  "entities": [
    {
      "name": "Habit",
      "fields": ["id", "name", "created_at"]
    },
    {
      "name": "HabitLog",
      "fields": ["id", "habit_id", "date", "completed"]
    }
  ],
  "relationships": [
    { "from": "HabitLog", "to": "Habit", "type": "many-to-one" }
  ]
}
```



## Project Status

This project was built as a scoped take-home assignment and is currently maintained as a portfolio piece rather than an actively developed product.

## Author

**Vaibhavi Jagadeesh Hiremath**
[GitHub](https://github.com/Vaib-raksh) · [LinkedIn](https://linkedin.com/in/vaibhavi-jagadeesh-hiremath)
