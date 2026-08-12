# Contributing

Contributions are welcome.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Before submitting

```bash
python -m unittest discover -s tests -v
ruff check ccna_lab_builder tests
```

## Adding a lab

Edit:

```text
ccna_lab_builder/data/scenarios.json
```

A scenario should include:

- unique two-digit ID
- name
- CCNA domain
- difficulty
- target duration
- objective
- tasks
- operational validation checks

Do not submit copyrighted Cisco images, exam dumps, confidential questions, passwords or real customer configurations.
