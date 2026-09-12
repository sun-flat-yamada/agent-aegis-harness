---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "architecture_doc"
id: "BLUEPRINT-MCP-AUDIT-001"
title: "MCP セキュリティゲートウェイ監査専従化 & マルチプラットフォーム汎用通知構想企画書 (Blueprint)"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: ".devs/changes/2026-09-12_mcp-audit-notification/blueprint.md"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.4.0"
tags: ["blueprint", "mcp", "audit-only", "notification", "multi-platform", "security-gateway"]
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
---

# MCP セキュリティゲートウェイ監査専従化 & マルチプラットフォーム汎用通知構想企画書 (Blueprint)

**Document ID:** BLUEPRINT-MCP-AUDIT-001 | **Version:** 1.0.0 | **Status:** Active | **Author:** @sun-flat-yamada (Youhei Yamada)  
**Target Change:** `.devs/changes/2026-09-12_mcp-audit-notification`  
**Parent Architecture:** [`docs/ARCHITECTURE.ja.md`](../../docs/ARCHITECTURE.ja.md) | **Related Guides:** [`docs/setup/target-project-guide.ja.md`](../../docs/setup/target-project-guide.ja.md)

---

## 1. 構想背景と課題提起

### 1.1 背景 (Context)
Agent Aegis Harness (`aah`) の MCP セキュリティゲートウェイ (`aah mcp-server`) は、AI エージェント（GitHub Copilot CLI, Claude Code, VS Code Copilot 等）が Model Context Protocol (MCP) を介して実行する各種ツール呼び出しを検査するインターフェースとして導入されました。

当初の暫定実装では、危険な操作（例: `rm -rf /` 等の破壊的コマンド実行）を検出した際に、JSON-RPC エラー（`-32000`）を返してツール実行を即時遮断（BLOCK）する設計となっていました。

### 1.2 課題とアンチパターン
しかし、MCP ツール連携における即時遮断は、以下の重大な運用摩擦および設計矛盾を生じさせます：
1. **開発者の自律フロー（Flow State）の破壊**:
   エージェントが高度な推論ループの中でツールを試行している際、外部ゲートウェイが問答無用でエラー遮断すると、エージェントがエラーハンドリングに失敗してループが異常終了するか、誤った自己修復を試みてコンテキストが破壊されます。
2. **MCP の本来の責務との乖離**:
   Aegis の MCP ゲートウェイの主眼は「5W1H 監査ログの正確な記録（Auditing & Traceability）」にあります。実行権限の遮断（Gating/Enforcement）は CI/CD ガバナンスやローカルのサンドボックス環境の責務であり、MCP 監査サーバーが独断で遮断を行うべきではありません。
3. **通知の欠如とブラックボックス化**:
   単にエラーコードを返すだけでは、ターミナルで作業している開発者や GUI エディタを使っているユーザーに「なぜ警告されたのか」「何が検出されたのか」が直感的に伝わりません。

したがって、**「MCP の監査機能はあくまで監査専従（Audit-Only）であり、ユーザー操作を即時遮断してはならない。危険な操作を検出した場合はユーザー通知を行うだけに留める」** という根本的な設計原則の転換が不可欠です。

---

## 2. 意思決定背景・判断基準・トレードオフ (ADR)

### ADR-1: 即時遮断（BLOCK）の完全撤廃と「監査専従 + ユーザー通知」への転換
- **決定**:
  `LocalMCPServer` において、`SentinelJudge` が `VerdictStatus.BLOCK` や `WARN` を下した場合でも、JSON-RPC エラーによるツール呼び出しの中断を行わない。
  代わりに以下の処理を実行する：
  1. WAL 監査ストアへ `status="FLAGGED"` として危険操作検出イベントを確実に永続化。
  2. マルチプラットフォーム通知を発行し、人間の開発者へ直ちに注意を促す。
  3. ツールレスポンス本文（`result.content`）に検閲警告メッセージを含め、正常応答としてエージェントへ返却する。
- **根拠**:
  自律エージェントの処理継続性を維持しつつ、背後で監査証跡を記録し、人間へ透明にアラートを届けることで、ガバナンスと開発者体験（DX）を両立する。

### ADR-2: 4 層ハイブリッド通知アーキテクチャの採用
- **要件**:
  OS: Windows / macOS / Linux  
  クライアント: VS Code (GUI/Chat), GitHub Copilot CLI (ターミナル), Claude Code (ターミナル), Cursor, ヘッドレス/CI/SSH
- **設計トレードオフ**:
  - デスクトップ通知のみに依存すると、SSH/CI やヘッドレス環境で失敗し、開発者に気付かれない。
  - `sys.stdout` に直接警告メッセージを出力すると、MCP の STDIO JSON-RPC 通信プロトコルが破壊される。
  - 外部のヘビーな GUI ライブラリ（PyQt, plyer 等）に依存すると、軽量・ポータブルな CLI であるべき `aah` の依存関係が肥大化する。
- **決定**:
  追加の外部依存を一切使用せず、Python 標準ライブラリのみで **4 層ハイブリッド通知** を実現する：
  1. **Layer 1 (STDERR & Terminal Bell)**: `sys.stderr` に ANSI カラー警告バナーを出力 + ターミナルベル `\a` によるアテンション喚起。
  2. **Layer 2 (MCP インバンド通知)**: ツールレスポンス本文に警告を注入し、AI チャット画面上でエージェント自身がユーザーへ注意喚起できるようにする。
  3. **Layer 3 (OS ネイティブ Toast 通知)**: Windows (PowerShell), macOS (osascript), Linux (notify-send) を非同期・非ブロッキングでベストエフォート実行。GUI がない環境では安全にスキップ。
  4. **Layer 4 (永続化アラートファイル)**: `.aegis/alerts.log` への追記。ファイルウォッチャーや後続の分析ツールと連携。

---

## 3. システムアーキテクチャ & コンポーネント設計

```mermaid
flowchart TD
    subgraph ClientLayer ["AI エージェント / 開発環境"]
        CopilotCLI["GitHub Copilot CLI<br/>(ターミナル)"]
        ClaudeCode["Claude Code<br/>(対話型 CLI)"]
        VSCode["VS Code / Cursor<br/>(GUI / Copilot Chat)"]
        SSHHeadless["CI / SSH Remote<br/>(ヘッドレス環境)"]
    end

    subgraph MCPGateway ["aah mcp-server (LocalMCPServer)"]
        STDIO["STDIO JSON-RPC Dispatcher"]
        Judge["SentinelJudge<br/>(Tier 1/2 ルール評価)"]
        Notifier["UniversalNotifier<br/>(汎用マルチレイヤー通知)"]
        WAL["SQLite WAL Store<br/>(ステータス: FLAGGED)"]
    end

    subgraph HybridNotification ["4 層ハイブリッド通知"]
        L1["Layer 1: STDERR + Terminal Bell (\\a)<br/>※ stdout を汚染せず即時表示"]
        L2["Layer 2: Tool Response Text<br/>※ AI がチャット画面でユーザーへ説明"]
        L3["Layer 3: OS Native Desktop Toast<br/>※ Win/Mac/Linux デスクトップ通知"]
        L4["Layer 4: Persistent Alert Log<br/>※ .aegis/alerts.log への追記"]
    end

    CopilotCLI -->|JSON-RPC request| STDIO
    ClaudeCode -->|JSON-RPC request| STDIO
    VSCode -->|JSON-RPC request| STDIO
    SSHHeadless -->|JSON-RPC request| STDIO

    STDIO --> Judge
    Judge -->|Verdict: BLOCK / WARN| Notifier
    Judge -->|Verdict: BLOCK / WARN| WAL

    Notifier --> L1
    Notifier --> L2
    Notifier --> L3
    Notifier --> L4

    L2 -->|JSON-RPC result (No error)| STDIO
    STDIO -->|JSON-RPC response| CopilotCLI
    STDIO -->|JSON-RPC response| ClaudeCode
    STDIO -->|JSON-RPC response| VSCode
    STDIO -->|JSON-RPC response| SSHHeadless
```

---

## 4. 期待される効果と検証方針
1. **ゼロ・ブロッキング**:
   エージェントがいかなる危険操作を伴う計画を策定・試行しても、MCP 層でツールが異常終了することはなく、エージェントの自律ループが不当に遮断されない。
2. **多面的なユーザー認識**:
   ターミナル、エディタ画面、OS デスクトップ、ログファイルのいずれの経路からでも、開発者は即座に危険操作の発生を察知できる。
3. **ドキュメントとの完全な整合性**:
   `docs/setup/target-project-guide.ja.md` および関連ガイドが、現実の実装および Aegis の監査原則と 100% 合致する。
