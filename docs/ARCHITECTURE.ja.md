---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc"
id: "DOC-ARCH-001-JA"
title: "Agent Aegis Harness アーキテクチャ & システム設計書"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: "docs/ARCHITECTURE.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.1.0"
tags: ["architecture", "sentinel", "archivist", "recorder", "refiner"]
---

# Agent Aegis Harness アーキテクチャ & システム設計書

## 1. システム構想
Agent Aegis Harness (`aah`) は、ソフトウェア開発AI（Google Antigravity, Claude Code, GitHub Copilot, Cursor 等）の挙動を透過的に計装・監査し、継続的に改善するための共通ガバナンス基盤です。開発者の日常業務に自然に装着され、決定論的再現性、暗号学的改ざん防止、3段階多層防御、およびオフライン自己改善を提供します。

```mermaid
flowchart TD
    subgraph HarnessExecution ["1. 実行・透過計装レイヤー"]
        Prompt["開発者プロンプト / CIトリガー"] --> Wrapper["aah wrap / Antigravity Hooks"]
        Wrapper --> Redactor["Sensitive Redactor (PII/Secret)"]
        Redactor --> Agent["AIエージェント"]
    end

    subgraph GovernanceLayer ["2. Sentinel & Archivist 統制レイヤー"]
        Agent --> Sentinel["Sentinel Judge (Tier 1 AST, Tier 2 Model)"]
        Sentinel --> Verdict{"判定: PASS / WARN / BLOCK"}
        Archivist["Archivist (Policy Hasher & Hash Chain)"] -.->|決定論的ハッシュ照合| Sentinel
    end

    subgraph AuditTrailLayer ["3. デュアルストリーム証跡 & テレメトリ"]
        Verdict --> Recorder["Aegis Recorder (5W1H抽出)"]
        Recorder --> CompactLog["audit-trail.jsonl (軽量台帳)"]
        Recorder --> ForensicLog["forensic-trail.jsonl (完全証跡)"]
        Recorder --> OTel["OpenTelemetry / 中央 SIEM"]
        Archivist -->|Hash Chain 封印| CompactLog
        Archivist -->|Hash Chain 封印| ForensicLog
    end

    subgraph OptimizationLayer ["4. Refiner (オフライン自己改善)"]
        CompactLog -.->|オフラインバッチ分析| Refiner["Cluster Analyzer & Patch Proposer"]
        Refiner --> PR["Rules / Skills 改善 Pull Request"]
    end
```

## 2. コアサブシステム仕様

### 2.1 Sentinel (リアルタイム監査・合否判定員)
- **Tier 1 (<10ms)**: インプロセスの高速 AST および正規表現フィルタリングにより、危険コマンド（再帰削除 `rm -rf /`、ディスクフォーマット、破壊操作）やホワイトリスト外ツールの実行を即時遮断（BLOCK）。
- **Sensitive Redactor**: ツール実行・ログ記録直前に、各種クラウドキー（OpenAI, GitHub, AWS）や認証トークン、IP、メールアドレスを自動マスキング。

### 2.2 Archivist (書記・暗号学的証明・再現性管理)
- **Policy Hasher**: `.aegis/rules/` および `.skills/` 内の全ポリシーファイルから正規化 SHA-256 ダイジェスト（`policy_hash_digest`）を算出・固定。
- **Hash Chain Manager**: 各ログ行が直前ブロックのハッシュを取り込む Merkle 連鎖（$H_i = \text{SHA256}(H_{i-1} + \text{Payload}_i)$）により、ログの1文字の改ざんや削除を数学的に即時検知。

### 2.3 Recorder (5W1H デュアルストリーム記録)
- **軽量監査ログ (`audit-trail.jsonl`)**: 日常の点検や高速検証に適したサマリーログ。
- **完全フォレンジックログ (`forensic-trail.jsonl`)**: プロンプト全文、推論トレース、ツール引数の完全な生証跡を保持。
- **独立連鎖保証**: 両ストリームが独立したハッシュチェーンを維持し、完全な暗号学的検証を保証。

### 2.4 Refiner (自己改善・最適化ループ)
- **疎結合運用**: 過去ログの監査判定再現性を保つため、監査実行時と自己改善を完全に分離したオフラインバッチとして動作。
- **Cluster Analyzer & Patch Proposer**: 蓄積ログを分析し、誤検知パターンの緩和やホワイトリスト更新の差分 PR を起票。
