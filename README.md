# Empório da Música — Customer Service Agent

Prototype of a text-based customer service agent for *Empório da Música*, a fictional
musical instrument store in Campo Grande/MS (Artefact AI Engineer technical case).

> Work in progress. Sections marked TODO are filled in as the project advances.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add your GEMINI_API_KEY
python -m emporio.cli       # TODO: available after the CLI commit
pytest                      # data-layer tests
```

## Technical decisions

TODO — agent approach, model/provider, retrieval for policies, prompt strategy,
interface, conversation persistence, data cleaning.

## Assumptions

TODO — e.g. how "days since delivery" is computed for the 7-day return window,
which contact details are used where the policy manual is inconsistent.

## Known limitations and next steps

TODO

## Use of AI coding assistants

TODO — state which assistant(s) were used and how (be specific and honest).

## Example conversations

See [`conversations/`](conversations/).
