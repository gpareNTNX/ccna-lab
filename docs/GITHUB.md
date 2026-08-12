# Publish to GitHub

## 1. Create an empty repository

Recommended name:

```text
ccna-eve-lab-builder
```

Do not initialize it with another README if you are pushing this generated project as-is.

## 2. Initialize locally

```bash
git init
git add .
git commit -m "Initial V4 release"
git branch -M main
```

## 3. Add your GitHub remote

```bash
git remote add origin <YOUR-GITHUB-REPOSITORY-URL>
git push -u origin main
```

## 4. Before every push

```bash
python -m unittest discover -s tests -v
```

Optional lint:

```bash
pip install -r requirements-dev.txt
ruff check ccna_lab_builder tests
```

## Repository safety

The `.gitignore` blocks common VM/vendor image extensions, including:

- `.qcow2`
- `.img`
- `.bin`
- `.iso`
- `.vmdk`
- `.ova`

Never commit Cisco images, passwords, EVE exports containing secrets, or production configurations.
