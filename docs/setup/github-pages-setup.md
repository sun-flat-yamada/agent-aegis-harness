---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-SETUP-PAGES-001"
title: "GitHub Pages Documentation Hosting Setup Guide"
version: "1.0.0"
status: "active"
language: "en"
canonical_ref: "docs/setup/github-pages-setup.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-13"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["setup", "github-pages", "documentation", "mkdocs", "ci-cd"]
---

# GitHub Pages Documentation Hosting Setup Guide

This guide explains the one-time manual configuration required on GitHub repository settings to enable the automated documentation publishing pipeline for `docs/`.

---

## 1. Overview & Architecture

Agent Aegis Harness uses **Material for MkDocs** along with modern GitHub Actions OIDC deployment (`actions/upload-pages-artifact@v5` and `actions/deploy-pages@v5`).

While the build, bilingual generation (English/Japanese), and artifact upload are fully automated via [`.github/workflows/pages.yml`](../../.github/workflows/pages.yml), **GitHub requires a one-time manual administrative action** to designate GitHub Actions as the publishing source for GitHub Pages.

---

## 2. One-Time Manual Setup Steps

Repository administrators must perform the following steps in the GitHub repository settings:

### Step 1: Open Pages Settings
1. Navigate to your repository on GitHub: `https://github.com/<owner>/<repo>`.
2. Click on the **Settings** tab in the top navigation bar.
3. In the left sidebar, under the **Code and automation** section, click on **Pages**.

### Step 2: Configure Build and Deployment Source
1. Under **Build and deployment**, locate the **Source** dropdown.
2. Change the Source from **Deploy from a branch** (default) to **GitHub Actions**.

> [!IMPORTANT]
> **Do NOT select a branch (e.g. `gh-pages` or `main/docs`).**  
> Aegis uses secure, branchless OIDC artifact deployment. Selecting **GitHub Actions** allows the `.github/workflows/pages.yml` workflow to publish directly to GitHub Pages without cluttering git branches.

### Step 3: Trigger the First Deployment
Once the source is set to **GitHub Actions**:
1. Push any commit to `main`, OR
2. Go to the **Actions** tab → Select **Deploy GitHub Pages Documentation** → Click **Run workflow** (`workflow_dispatch`).

### Step 4: Verify Live Publication
When the workflow run succeeds:
1. Return to **Settings → Pages**.
2. You will see the active deployment status:  
   `Your site is live at https://<owner>.github.io/<repo>/`
3. Visit the URL to confirm that the bilingual site (English `/` and Japanese `/ja/`) and the client-side search are functioning properly.

---

## 3. Local Preview & Development

For local editing and previewing of documentation:

```bash
# Install documentation dependencies
make install-docs
# or: pip install -e ".[docs]"

# Start local live-reloading preview server (http://127.0.0.1:8000)
make docs-serve

# Run strict build validation (link and syntax checks)
make docs-build
```
