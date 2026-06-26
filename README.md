# Resume Site Tool

Turn a resume into a fixed-template GitHub Pages personal website.

The important design choice is that the model never designs pages. It only fills
a fixed `ResumeData` schema. The website is rendered by one of three committed,
stable templates.

## Templates

- `engineer-clean`: software, backend, full-stack, AI and data engineers.
- `research-academic`: academic profiles, research assistants, publications.
- `product-modern`: product, founder, consulting and generalist profiles.

## Quick Start

```bash
cd resume-site-tool
./run.sh
```

Open:

```text
http://127.0.0.1:8000
```

Set one of these for high-quality resume parsing:

```bash
export OPENAI_API_KEY=sk-...
```

or:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Without an API key, the tool uses a limited local parser. That is enough to test
the templates and full flow, but production quality needs an LLM provider.

## Public Access

`http://127.0.0.1:8000` is local-only. To let other people access the interface,
deploy it as a public web service. This project includes:

- `Dockerfile`
- `Procfile`
- `.env.example`
- `deploy.md`

Read `deploy.md` for Render/Railway/Fly/Cloud Run and tunnel options.

中文公网部署说明见 `PUBLIC_DEPLOY_zh.md`。

## CLI Usage

Generate from existing structured JSON:

```bash
python scripts/generate_cli.py samples/arthur.json engineer-clean out/arthur
```

Parse a resume into JSON:

```bash
python scripts/parse_cli.py path/to/resume.pdf -o generated/resume-data.json
```

Parse and render in one command:

```bash
python scripts/build_from_resume.py path/to/resume.pdf --template engineer-clean -o generated/site
```

## Publish to GitHub Pages

Publish a generated site to `username/username.github.io`:

```bash
export GITHUB_TOKEN=ghp_...
python scripts/publish_github_pages.py generated/site username
```

Token permissions:

- Classic PAT: `public_repo`
- Fine-grained PAT: selected repo with `Contents: Read and write`

Repository rules:

- For a personal root site, use a public repo named `username.github.io`.
- The repo may be completely empty. The publisher will create the first commit.
- If the repo does not exist and you use a fine-grained token, create the repo
  first because fine-grained tokens generally cannot create new repositories.

In the web UI, a successful publish shows the direct website URL first, with a
copy button. GitHub Pages can take 30-120 seconds before the URL is reachable.

## Generated Site Structure

```text
site/
  index.html
  README.md
  .nojekyll
  .resume-site.json
  assets/
    styles.css
    main.js
    resume-data.js
    profile.svg
```

## Productization Notes

For a real multi-user product, replace raw token input with GitHub OAuth or a
GitHub App. Keep the same internal pipeline:

```text
resume file -> text -> ResumeData JSON -> fixed template -> GitHub Pages
```

Do not store resume files or GitHub tokens longer than necessary. Let users
choose which contact fields are public before publishing.
