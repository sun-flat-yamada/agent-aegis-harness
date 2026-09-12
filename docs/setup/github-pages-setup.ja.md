---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-SETUP-PAGES-001-JA"
title: "GitHub Pages ドキュメント公開セットアップ手順書"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: "docs/setup/github-pages-setup.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-13"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["setup", "github-pages", "documentation", "mkdocs", "ci-cd"]
---

# GitHub Pages ドキュメント公開セットアップ手順書

本ガイドは、Agent Aegis Harness (`aah`) の `docs/` 配下のドキュメント群を GitHub Pages 上へ自動公開するために必要な、**GitHub リポジトリ側での 1 回限りの手動設定手順**を解説します。

---

## 1. 概要とデプロイ方式

本リポジトリでは、静的サイト生成エンジンとして **Material for MkDocs** を採用し、最新の GitHub Actions ネイティブな OIDC アーティファクトデプロイ（`actions/upload-pages-artifact@v5` および `actions/deploy-pages@v5`）を利用しています。

ビルド、日英バイリンガル展開（英語・日本語）、アーティファクトの生成は [`.github/workflows/pages.yml`](../../.github/workflows/pages.yml) によって完全に自動化されていますが、**GitHub のセキュリティ仕様上、リポジトリ管理者によるデプロイ元（Source）の手動切り替えが初回に 1 回だけ必要**となります。

---

## 2. 初回手動設定手順（ワンタイム）

リポジトリ管理者は、GitHub の Web 画面にて以下の操作を行ってください：

### Step 1: リポジトリの Pages 設定画面を開く
1. 対象の GitHub リポジトリ（`https://github.com/<owner>/<repo>`）を開きます。
2. 上部タブの **Settings**（歯車アイコン）をクリックします。
3. 左サイドバーの **Code and automation** セクションにある **Pages** をクリックします。

### Step 2: Build and deployment の Source を変更する
1. **Build and deployment** エリアにある **Source** ドロップダウンを確認します。
2. デフォルトの `Deploy from a branch` から **`GitHub Actions`** に切り替えます。

> [!IMPORTANT]
> **ブランチ（`gh-pages` や `main/docs` など）は選択しないでください。**  
> Aegis ではブランチ履歴を汚さない OIDC アーティファクト方式を採用しています。Source を **`GitHub Actions`** に設定することで、ワークフローが直接安全にデプロイを行えるようになります。

### Step 3: 初回デプロイの実行
Source を `GitHub Actions` に変更したら、以下のいずれかでデプロイをトリガーします：
1. `main` ブランチに任意のコミットを push する、または
2. GitHub 上の **Actions** タブ → **Deploy GitHub Pages Documentation** を選択 → **Run workflow** ボタンをクリック（手動実行）。

### Step 4: サイトの公開確認
ワークフローが完了すると：
1. 再度 **Settings → Pages** を開くと、以下のように公開 URL が表示されます：  
   `Your site is live at https://<owner>.github.io/<repo>/`
2. URL にアクセスし、トップページ、日本語版（`/ja/`）、Mermaid 図、全文検索が正常に動作することを確認します。

---

## 3. ローカルでのプレビュー & 開発手順

ドキュメントの執筆や編集時に、ローカル PC 上でリアルタイムプレビューを行う手順です：

```bash
# ドキュメント用パッケージのインストール
make install-docs
# または: pip install -e ".[docs]"

# ローカルプレビューサーバーの起動 (http://127.0.0.1:8000 でホットリロード)
make docs-serve

# 厳格ビルド検証（リンク切れ・構文チェック）
make docs-build
```
