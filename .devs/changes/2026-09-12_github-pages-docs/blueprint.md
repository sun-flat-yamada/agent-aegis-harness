---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc"
id: "DOC-PAGES-BP-001"
title: "GitHub Pages ドキュメント公開基盤 構想企画 & ADR (blueprint)"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: ".devs/changes/2026-09-12_github-pages-docs/blueprint.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor"]
  min_aah_version: "0.1.0"
tags: ["documentation", "github-pages", "mkdocs-material", "ci-cd"]
---

# GitHub Pages ドキュメント公開基盤 構想企画 & ADR (blueprint)

## 1. 変更の背景と目的

Agent Aegis Harness (`aah`) は、AI エージェント運用のための厳格なガバナンス・監査・自動進化基盤です。
現在、[`docs/`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/docs) 配下に以下のような高品位なドキュメント群が日英バイリンガルで整備されています：
- 全体アーキテクチャ設計書 (`ARCHITECTURE.md` / `ARCHITECTURE.ja.md`)
- アーキテクチャ意思決定レコード (`adr/0001-...` 〜 `adr/0003-...`)
- 運用ガイドライン (`operations/audit-workflows.md` 等)
- セットアップガイド (`setup/target-project-guide.md` 等)

しかしながら、現時点ではこれらを Web サイトとして閲覧・検索できる **GitHub Pages 公開機能が未実装** であり、利用者は GitHub のリポジトリブラウザ上で個別の Markdown を手動で巡回して読まなければならない状態です。

本変更の目的は、**最新・高信頼（高Star/高採用数）** な静的ドキュメント生成エンジンを選定し、`docs/` 以下のドキュメント資産を検索性・視認性・保守性に優れた Web サイトとして GitHub Pages 上へ自動公開する CI/CD パイプラインを確立することです。

---

## 2. 意思決定背景・判断基準・トレードオフ (ADR)

### ADR-1: 静的ドキュメントサイト生成ツールの選定

#### 調査・比較対象（2026年9月最新データに基づく比較）

| ツール / フレームワーク | GitHub Stars | 主要言語 / エコシステム | メリット | デメリット / 採用見送り理由 |
| :--- | :---: | :--- | :--- | :--- |
| **Material for MkDocs** (`squidfunk/mkdocs-material`) | **27.4k+** | **Python** | ・Python プロジェクトとの親和性が極めて高く、Node.js 不要<br>・設定が `mkdocs.yml` 単一で極めて簡潔<br>・クライアントサイド高速検索内蔵<br>・Mermaid 図ネイティブ描画<br>・モダン UI（ダークモード、タブ、レスポンシブ）<br>・日英バイリンガル対応（`mkdocs-static-i18n` による `*.md` / `*.ja.md` 直結サポート） | 独自の React コンポーネントを埋め込むような高度な動的カスタマイズは限定的（本用途では不要） |
| **Docusaurus** (`facebook/docusaurus`) | 66.2k+ | TypeScript / React | ・圧倒的スター数<br>・React コンポーネント埋め込み自由度 | ・Node.js / npm / Yarn エコシステムが必須<br>・Python 純粋リポジトリに Node 依存が混入し CI と保守が複雑化 |
| **VitePress** (`vuejs/vitepress`) | 18.3k+ | TypeScript / Vue | ・Vite 駆動でビルドが超高速<br>・Vue エコシステムとの親和性 | ・Node.js 環境が必須<br>・Python リポジトリ管理コストの増大 |
| **Starlight** (`withastro/starlight`) | 9.2k+ | TypeScript / Astro | ・Astro ベースで高速・最新モダン | ・Node.js 環境が必須 |
| **Sphinx** (`sphinx-doc/sphinx`) | 8.0k+ | Python | ・Python 伝統の標準ツール | ・設定（`conf.py`）が複雑で重厚<br>・Markdown (MyST) やモダンな UI テーマ、検索の導入障壁が高い |

#### 決定 (Decision)
**`Material for MkDocs (mkdocs-material)` を採用する。**

#### 選定根拠 (Rationale)
1. **エコシステムの一致**: 本プロジェクトは Python 3.10+ / `pyproject.toml` / `hatchling` で構成されており、CI も Python 環境で一元化されている。Node.js への追加依存を持ち込まず、`pip install ".[docs]"` だけでローカルプレビューおよび CI ビルドが完結する。
2. **圧倒的な実績と信頼性**: Python ドキュメントフレームワークとして 27,400+ Stars を獲得し、FastAPI, Pydantic, Ruff, Typer, Prefect 等の現代的な Python 主要 OSS の事実上の標準（デファクトスタンダード）となっている。
3. **既存 Markdown 資産の完全活用**: すでに記述されている Mermaid 図、GitHub 風のアラート、数式、コードブロックをそのまま美しくレンダリングできる。
4. **日英バイリンガル構造への完全適合**: 本リポジトリの命名規則（`foo.md` と `foo.ja.md`）は、標準的な `mkdocs-static-i18n` プラグインの動作原理（suffix方式）と 100% 合致しており、言語切替スイッチャーを最小限の設定で提供できる。

---

### ADR-2: GitHub Pages デプロイ方式の選定

#### 比較検討
- **方式 A: レガシー方式 (`gh-pages` ブランチ push)**
  - リモートに `gh-pages` ブランチを作成し、コミットを積み上げる方式。
  - Git リポジトリの履歴肥大化やコンフリクト、ブランチ保護ルールの煩雑化が生じる。
- **方式 B: 最新推奨方式 (GitHub Actions ネイティブ OIDC & Pages Artifact デプロイ)**
  - GitHub 公式の最新アクションを使用：
    - `actions/configure-pages@v6`
    - `actions/upload-pages-artifact@v5`
    - `actions/deploy-pages@v5`
  - 専用ブランチを汚さず、安全な OIDC 署名トークン（`id-token: write`）により GitHub Pages 基盤へ直接成果物（tar archive）を安全かつ決定論的にデプロイする。

#### 決定 (Decision)
**方式 B（GitHub Actions ネイティブ Pages デプロイ）を採用する。**

---

## 3. システムアーキテクチャ & パイプライン構成

```mermaid
flowchart TD
    subgraph Repo ["agent-aegis-harness Repository"]
        MD ["docs/ (*.md & *.ja.md)"]
        CONF ["mkdocs.yml (Theme, Plugins, Nav, i18n)"]
        CONF_EXT ["pyproject.toml [project.optional-dependencies.docs]"]
    end

    subgraph CI ["GitHub Actions (.github/workflows/pages.yml)"]
        Trigger["Push to main / Workflow Dispatch"]
        Setup["Set up Python 3.10 & Install deps (mkdocs-material, etc.)"]
        Build["mkdocs build --strict -> site/"]
        Upload["actions/upload-pages-artifact@v5"]
        Deploy["actions/deploy-pages@v5"]
    end

    subgraph Hosting ["GitHub Pages Service (OIDC Secured)"]
        LiveSite["https://sun-flat-yamada.github.io/agent-aegis-harness/"]
        EN["English Documentation (/en/)"]
        JA["日本語ドキュメント (/ja/)"]
        Search["Lunr Client-Side Full-text Search"]
    end

    Trigger --> Setup
    MD --> Build
    CONF --> Build
    CONF_EXT --> Setup
    Setup --> Build
    Build --> Upload
    Upload --> Deploy
    Deploy --> Hosting
    Hosting --> LiveSite
    LiveSite --> EN
    LiveSite --> JA
    LiveSite --> Search
```

---

## 4. コンポーネント役割と仕様ドラフト

1. **ドキュメント設定ファイル ([`mkdocs.yml`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/mkdocs.yml))**
   - サイト名: `Agent Aegis Harness`
   - テーマ: `material`
   - プラグイン:
     - `search` (全文検索、言語トークナイザー対応)
     - `i18n` (`mkdocs-static-i18n`: default `en`, alternate `ja`)
   - Markdown 拡張:
     - `admonition` (警告・注意ブロック)
     - `pymdownx.superfences` (Mermaid ダイアグラムのネイティブ描画)
     - `pymdownx.highlight` (シンタックスハイライト)
     - `pymdownx.inlinehilite`
     - `pymdownx.tabbed` (タブ切替)
     - `pymdownx.snippets`
     - `tables`, `attr_list`, `md_in_html`
   - ナビゲーション構成 (`nav`):
     - Home (Overview)
     - Architecture & Design
     - Architecture Decision Records (ADR)
     - Operations & Workflows
     - Setup & Quickstart

2. **トップページ ([`docs/index.md`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/docs/index.md) & [`docs/index.ja.md`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/docs/index.ja.md))**
   - 既存の `README.md` および `README.ja.md` のエッセンスを反映し、ポータルサイトとしての導入・クイックスタート・目次リンクを完備。
   - `frontmatter.schema.json` に適合する YAML フロントマターを付与。

3. **依存定義 ([`pyproject.toml`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/pyproject.toml))**
   - `[project.optional-dependencies]` に `docs` グループを追加：
     - `mkdocs-material>=9.5.0`
     - `mkdocs-static-i18n>=1.2.0`

4. **CI/CD ワークフロー ([`.github/workflows/pages.yml`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/.github/workflows/pages.yml))**
   - トリガー: `main` ブランチへの push、および手動実行（`workflow_dispatch`）
   - パーミッション: `contents: read`, `pages: write`, `id-token: write`
   - 並行制御: `concurrency: group: "pages", cancel-in-progress: false`
   - ステップ: Checkout → Python 3.10 セットアップ → `pip install -e ".[docs]"` → `mkdocs build --strict` → `upload-pages-artifact` → `deploy-pages`

5. **開発用コマンド ([`Makefile`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/Makefile))**
   - `docs-serve`: ローカルプレビュー起動（ホットリロード）
   - `docs-build`: 静的ビルドテスト

---

## 5. ブートストラップ手順

1. 仮想環境への依存ライブラリのインストール確認
2. `docs/index.md` および `docs/index.ja.md` の作成（スキーマ適合検証）
3. `mkdocs.yml` の配置
4. `mkdocs build --strict` によるローカル検証（リンク切れ、ビルドエラーなしの確認）
5. `.github/workflows/pages.yml` の定義
6. CI フロントマターリント（`frontmatter-linter.yml` 相当のスクリプト）とテストの完全通過確認
