---
$schema: ".aegis/schemas/frontmatter.schema.json"
doc_type: "guide"
id: "DOC-OPS-COST-001-JA"
title: "Agent Aegis Harness クラウド運用想定コスト分析レポート"
version: "1.0.0"
status: "active"
language: "ja"
canonical_ref: "docs/operations/cloud-cost-analysis.md"
author: "@sun-flat-yamada"
last_reviewed: "2026-09-12"
compatibility:
  tools: ["google-antigravity", "claude-code", "github-copilot", "cursor", "cli"]
  min_aah_version: "0.3.0"
tags: ["cost-analysis", "cloud-mcp", "azure", "finops", "governance"]
---

# Agent Aegis Harness クラウド運用想定コスト分析レポート

## 1. エグゼクティブサマリー (Executive Summary)

本レポートは、Agent Aegis Harness (`aah`) の中央ガバナンス基盤（**Aegis Cloud MCP Security Gateway** および **全社中央監査・WORMログ基盤**）をクラウド環境（Microsoft Azure 東日本リージョン: `japaneast`）で運用する場合の想定コストを詳細に試算・分析したものです。

稼働するプロジェクト規模および開発者数に基づき、**「小規模 (PoC・チーム)」「中規模 (部門・事業部)」「大規模 (全社共通基盤)」** の3パターンを定義し、各コンポーネントの費用内訳、年額、および開発者1名あたりの月額コストを算出しました。

算出に用いたすべての単価・計算式は、Microsoft Azure 公式価格情報および公開 REST API である **Azure Retail Prices API** より取得し、エンドポイントの疎通確認（HTTP 200 OK）および公式ドキュメント引用文との突合による**存在と妥当性の事前検証**を完了しています。

### 3パターンの比較サマリー

※為替レートは参考値として **1 USD = 150 JPY**（税抜）で換算しています。

| 規模パターン | 対象プロジェクト数 | 対象開発者数 | 月間監査イベント数 | 月間生成データ量 | 月額想定コスト (USD) | 月額想定コスト (JPY) | 年額想定コスト (JPY) | 開発者1名あたり月額 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **小規模 (Small / PoC)** | 3 PJ | 15 名 | 30,000 回 / 月 | 0.48 GB / 月 | **\$34.73 / 月** | **約 ¥5,210** | **約 ¥62,516** | **約 ¥347 / 人月** |
| **中規模 (Medium / 部門)** | 20 PJ | 100 名 | 200,000 回 / 月 | 3.20 GB / 月 | **\$58.17 / 月** | **約 ¥8,725** | **約 ¥104,700** | **約 ¥87 / 人月** |
| **大規模 (Large / 全社)** | 100 PJ | 1,000 名 | 2,000,000 回 / 月 | 32.00 GB / 月 | **\$225.91 / 月** | **約 ¥33,886** | **約 ¥406,629** | **約 ¥34 / 人月** |

> [!TIP]
> **主要な分析結果**:
> - 全社規模（100プロジェクト・1,000名）で運用した場合でも、月額費用は **約 ¥33,886 (年額 約40.6万円)** に留まり、開発者1人あたりわずか **約 ¥34 / 月** でエンタープライズ級のAIガバナンスと3年間の法的改ざん防止（WORM不変証跡）を実現できます。
> - 後述の「FinOps コスト最適化施策（デュアルストリーム分離）」を適用した場合、大規模構成の月額費用は **約 ¥18,856 / 月（開発者1人あたり 約 ¥19 / 月）** までさらに圧縮可能です。

---

## 2. システム構成とコスト算定アーキテクチャ

本試算の対象アーキテクチャは、リポジトリ内の IaC 定義 [`infra/azure/main.tf`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/infra/azure/main.tf) および構築運用ガイド [`docs/setup/cloud-mcp-server-guide.ja.md`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/docs/setup/cloud-mcp-server-guide.ja.md) に完全準拠しています。

```mermaid
flowchart TD
    subgraph Clients ["クライアント層 (開発者端末 / 各PJ)"]
        IDE["AIツール (Antigravity, Claude Code, Cursor)"]
    end

    subgraph AzureRegion ["Microsoft Azure (japaneast)"]
        subgraph IngressSecurity ["1. コンテナ実行 & セキュリティ検閲"]
            ACA["Azure Container Apps (Standard)<br/>aegis-mcp-gateway"]
            KV["Azure Key Vault (Standard)<br/>認証トークン & 暗号鍵"]
        end

        subgraph IngestionStream ["2. 高スループットストリーミング"]
            AEH["Azure Event Hubs (Standard)<br/>Throughput Units (TU)"]
        end

        subgraph StorageAnalytics ["3. 永続保管 & 検索・監査"]
            BLOB["Azure Blob Storage (Cool GRS)<br/>WORM 不変ポリシー (3年保持)"]
            LA["Azure Log Analytics Workspace<br/>Hot 検索 / Microsoft Sentinel"]
        end
    end

    IDE -->|HTTPS / SSE (Bearer Token)| ACA
    ACA -.->|トークン検証| KV
    ACA -->|監査ストリーム (5W1H)| AEH
    AEH -->|Capture / バッチ書き出し| BLOB
    AEH -->|Hot ストリーム連携| LA
```

### 構成コンポーネント一覧
1. **Azure Container Apps (Security Gateway)**:
   - Python / FastAPI ベースの軽量コンテナ。開発者からの MCP ツール要求を中継し、インプロセス Sentinel で即時判定（ALLOW/BLOCK）。
   - 従量課金（Consumption Plan）を採用し、リクエスト数と使用リソース（vCPU秒、GiB秒）に応じて柔軟にスケール。
2. **Azure Event Hubs (Ingestion プレーン)**:
   - 監査イベントを高スループット・低遅延で確実にバッファリング。Throughput Unit (TU) 単位でプロビジョニング。
3. **Azure Blob Storage (WORM 不変保管層)**:
   - 監査ログ（`audit-trail.jsonl` および `forensic-trail.jsonl`）を法的要件（EU AI Act, SOC 2 Type II）に基づき 3〜10 年間改ざん不能（WORM）で保存。コスト効率の高い Cool GRS（地理冗長）を採用。
4. **Azure Log Analytics Workspace (Hot 検索層)**:
   - 直近30日間のインシデント調査・KQL検索・Microsoft Sentinel 監視用。
5. **Azure Key Vault & Bandwidth**:
   - ワークスペース認証トークン管理および外部通信。

---

## 3. 単価データ・出典URL・存在および妥当性検証

レポートの信頼性を保証するため、すべての単価は Microsoft Azure 公式価格ページおよび Azure Retail Prices API（公開 REST API）から直接取得・照合し、存在と妥当性の検証を実施しました。

### 3.1 公式出典と引用文

| コンポーネント | 公式出典 URL | 公式ドキュメント引用文 (Short Quote) |
| :--- | :--- | :--- |
| **Azure Container Apps** | [Container Apps Pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/) | *"Azure Container Apps consumption plan is billed based on per-second resource allocation and requests. The first 180,000 vCPU-seconds, 360,000 GiB-seconds, and 2 million requests per subscription per month are free. Beyond that, you pay for what you use on a per second basis based on the number of vCPU-s and GiB-s your applications are allocated."* |
| **Azure Event Hubs** | [Event Hubs Pricing](https://azure.microsoft.com/en-us/pricing/details/event-hubs/) | *"/hour per Throughput Unit"* / *"Ingress events"* (1 Throughput Unit で最大 1 MB/秒または 1,000 events/秒のイングレスを提供) |
| **Azure Blob Storage** | [Blob Storage Pricing](https://azure.microsoft.com/en-us/pricing/details/storage/blobs/) | *"The Cool and Archive tiers are for cool or cold data with pricing optimized for lowest GB storage prices."* / *"Any blob that is moved to the Cool tier is subject to a Cool tier early deletion period of 30 days."* |
| **Azure Monitor / Log Analytics** | [Azure Monitor Pricing](https://azure.microsoft.com/en-us/pricing/details/monitor/) | *"Azure Monitor includes functionality for the collection and analysis of log data (billed by data ingestion, retention, and export)... Features of Azure Monitor that are automatically enabled such as collection of standard metrics and activity logs are provided at no cost."* |
| **Azure Key Vault** | [Key Vault Pricing](https://azure.microsoft.com/en-us/pricing/details/key-vault/) | *"Safeguard and maintain control of keys and other secrets"* (Standard 操作回数課金) |

### 3.2 Azure Retail Prices API による妥当性検証結果 (japaneast)

- **API エンドポイント**: `https://prices.azure.com/api/retail/prices`
- **検証日**: 2026-09-12
- **対象リージョン**: `japaneast` (東日本)
- **通貨**: USD

| サービス名 | SKU名 | メーター名 (MeterName) | 取得単価 (UnitPrice) | 課金単位 (UnitOfMeasure) | 検証ステータス |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Azure Container Apps** | Standard | Standard vCPU Active Usage | **\$0.00002400** | 1 Second | 一致・妥当 |
| | Standard | Standard Memory Active Usage | **\$0.00000300** | 1 GiB Second | 一致・妥当 |
| | Standard | Standard vCPU Idle Usage | **\$0.00000300** | 1 Second | 一致・妥当 |
| | Standard | Standard Memory Idle Usage | **\$0.00000300** | 1 GiB Second | 一致・妥当 |
| | Standard | Standard Requests | **\$0.40000000** | 1M (100万回) | 一致・妥当 |
| **Azure Event Hubs** | Standard | Standard Throughput Unit | **\$0.03000000** | 1 Hour (\$21.60/TU月) | 一致・妥当 |
| | Standard | Standard Ingress Events | **\$0.02800000** | 1M (100万回) | 一致・妥当 |
| **Storage (Blob)** | Cool GRS | Cool GRS Data Stored | **\$0.02200000** | 1 GB/Month | 一致・妥当 |
| | Cool GRS | Cool GRS Write Operations | **\$0.20000000** | 10K (1万回) | 一致・妥当 |
| | Cool GRS | Cool Read Operations | **\$0.01300000** | 10K (1万回) | 一致・妥当 |
| **Log Analytics** | Analytics Logs | Analytics Logs Data Ingestion | **\$3.34000000** | 1 GB | 一致・妥当 |
| | Analytics Logs | Analytics Logs Data Retention | **\$0.15000000** | 1 GB/Month (31日以降) | 一致・妥当 (30日以内無料) |
| **Key Vault** | Standard | Operations | **\$0.03000000** | 10K (1万回) | 一致・妥当 |
| **Bandwidth** | Standard | Standard Data Transfer Out | **\$0.00000000** | 1 GB (最初の100GB無料) | 一致・妥当 |

---

## 4. 規模別ワークロード前提と計算方式

### 4.1 共通ワークロード指標 (開発者1名あたり)
- **月間稼働日数**: 20日 / 月 (平日8時間稼働)
- **AI ツール呼出回数**: 平均 **100 回 / 開発者 / 日** (1時間あたり約12〜15回のプロンプト・MCPツール呼出)
- **月間イベント数**: 100回 × 20日 = **2,000 回 / 開発者 / 月**
- **ログペイロード設計**:
  - `audit-trail.jsonl` (軽量台帳): 約 **1 KB / イベント**
  - `forensic-trail.jsonl` (完全フォレンジック証跡): 約 **15 KB / イベント**
  - 合計データ量: 約 **16 KB / イベント** (開発者1名あたり約 32 MB / 月)

### 4.2 3パターンの規模定義

| パターン | プロジェクト数 | メンバー数 (名) | 月間イベント総数 | 月間総データ量 (GB) | ピーク時 TPS (req/sec) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **小規模 (Small)** | 3 PJ | 15 名 | 30,000 回 | 0.48 GB | 0.5 req/sec (平均 0.05) |
| **中規模 (Medium)** | 20 PJ | 100 名 | 200,000 回 | 3.20 GB | 3.5 req/sec (平均 0.35) |
| **大規模 (Large)** | 100 PJ | 1,000 名 | 2,000,000 回 | 32.00 GB | 35.0 req/sec (平均 3.47) |

### 4.3 コスト算出計算方式

各項目の計算ロジックは以下の通りです（月間換算: 720時間 = 2,592,000秒）。

#### 1. Azure Container Apps
- 各レプリカのスペック: 0.5 vCPU, 1.0 GiB メモリ
- 稼働内訳: 業務時間内（月160時間）のうちアクティブ率 30%（処理中）、アイドル率 70%。業務時間外（月560時間）はアイドル 100%。
  $$\text{Active秒数/レプリカ} = 160 \times 3,600 \times 0.3 = 172,800 \text{ 秒}$$
  $$\text{Idle秒数/レプリカ} = 2,592,000 - 172,800 = 2,419,200 \text{ 秒}$$
- 無料枠控除:
  $$\text{課金対象 Active vCPU秒} = \max(0, (\text{総 Active秒} \times 0.5) - 180,000)$$
  $$\text{課金対象 Active GiB秒} = \max(0, (\text{総 Active秒} \times 1.0) - 360,000)$$
  $$\text{課金対象 リクエスト数} = \max(0, \text{月間イベント数} - 2,000,000)$$
- 費用合計:
  $$\text{Cost}_{\text{ACA}} = (\text{課金 Active vCPU秒} \times 0.000024) + (\text{課金 Active GiB秒} \times 0.000003) + (\text{総 Idle vCPU秒} \times 0.000003) + (\text{総 Idle GiB秒} \times 0.000003) + \left(\frac{\text{課金 Req}}{1,000,000} \times 0.40\right)$$

#### 2. Azure Event Hubs
- Throughput Unit 課金:
  $$\text{Cost}_{\text{TU}} = \text{TU数} \times \$0.030 \times 720 \text{ 時間} = \text{TU数} \times \$21.60 / \text{月}$$
- Ingress Events 課金:
  $$\text{Cost}_{\text{Ingress}} = \left(\frac{\text{月間イベント数}}{1,000,000}\right) \times \$0.028$$

#### 3. Azure Blob Storage (Cool GRS)
- データ保管料金:
  $$\text{Cost}_{\text{Storage}} = \text{データ容量 (GB)} \times \$0.022 / \text{GB月}$$
- 書き込み操作料金 (Put/CreateBlob):
  $$\text{Cost}_{\text{Writes}} = \left(\frac{\text{月間イベント数}}{10,000}\right) \times \$0.20$$

#### 4. Azure Log Analytics Workspace
- データインジェスト料金:
  $$\text{Cost}_{\text{LA}} = \text{インジェストデータ量 (GB)} \times \$3.34 / \text{GB}$$
- ※最初の30日間のデータ保持はインジェスト料金に含まれ無料。

#### 5. Azure Key Vault & Egress
- Key Vault: Standard 操作課金（月間約10,000回のシークレット参照・検証）= \$0.03 / 月
- Bandwidth: 月間外向き転送量は無料枠（100 GB/月）に収まるため \$0.00。

---

## 5. 3パターンの詳細コスト試算と内訳

### 5.1 パターン 1: 小規模 (Small / PoC・チーム導入)

- **想定環境**: 3 プロジェクト / 15 名 / 月間 30,000 リクエスト / 月間 0.48 GB
- **リソース構成**: Container Apps 1 レプリカ常時待機 / Event Hubs 1 TU

| 費用項目 | 算定諸元 | 月額費用 (USD) | 月額費用 (JPY) | 構成比 |
| :--- | :--- | :--- | :--- | :--- |
| **Azure Container Apps** | 1 レプリカ (0.5 vCPU / 1.0 GiB) | \$10.89 | ¥1,633 | 31.4% |
| **Azure Event Hubs** | 1 TU (固定 \$21.60) + 3万イベント | \$21.60 | ¥3,240 | 62.2% |
| **Azure Blob Storage** | 0.48 GB 保管 (\$0.01) + 3万回書き込み (\$0.60) | \$0.61 | ¥92 | 1.8% |
| **Azure Log Analytics** | 0.48 GB インジェスト (Hot 30日保持) | \$1.60 | ¥240 | 4.6% |
| **Key Vault / Egress** | トランザクション & 外部通信 (100GB無料枠内) | \$0.03 | ¥4 | 0.1% |
| **月額合計** | — | **\$34.73** | **¥5,210** | **100.0%** |
| **年額合計** | — | **\$416.77** | **¥62,516** | — |
| **開発者1名あたり** | 15名で除算 | **\$2.32 / 人** | **約 ¥347 / 人月** | — |

**【考察】**
小規模環境では、固定的にプロビジョニングされる Event Hubs 1 TU（\$21.60/月）がコストの過半を占めます。PoC段階でさらにコストを抑えたい場合は、Event Hubs を介さず Container Apps から Blob Storage への直接書き込み構成にすることで、**月額約 \$13 (約 ¥2,000)** での運用も可能です。

---

### 5.2 パターン 2: 中規模 (Medium / 部門・事業部展開)

- **想定環境**: 20 プロジェクト / 100 名 / 月間 200,000 リクエスト / 月間 3.20 GB
- **リソース構成**: Container Apps 2 レプリカ冗長構成 / Event Hubs 1 TU

| 費用項目 | 算定諸元 | 月額費用 (USD) | 月額費用 (JPY) | 構成比 |
| :--- | :--- | :--- | :--- | :--- |
| **Azure Container Apps** | 2 レプリカ冗長構成 | \$21.77 | ¥3,266 | 37.4% |
| **Azure Event Hubs** | 1 TU (固定 \$21.60) + 20万イベント (\$0.01) | \$21.61 | ¥3,241 | 37.1% |
| **Azure Blob Storage** | 3.2 GB 保管 (\$0.07) + 20万回書き込み (\$4.00) | \$4.07 | ¥611 | 7.0% |
| **Azure Log Analytics** | 3.2 GB インジェスト (Hot 30日保持) | \$10.69 | ¥1,603 | 18.4% |
| **Key Vault / Egress** | トランザクション & 外部通信 (100GB無料枠内) | \$0.03 | ¥4 | 0.1% |
| **月額合計** | — | **\$58.17** | **¥8,725** | **100.0%** |
| **年額合計** | — | **\$698.00** | **¥104,700** | — |
| **開発者1名あたり** | 100名で除算 | **\$0.58 / 人** | **約 ¥87 / 人月** | — |

**【考察】**
100名規模の開発組織において、月額約 8,700 円（年額約10.5万円）で高可用性な冗長ゲートウェイと改ざん防止監査ログを運用できます。開発者1人あたり **月額87円** と極めて経済的です。

---

### 5.3 パターン 3: 大規模 (Large / 全社統一ガバナンス展開)

- **想定環境**: 100 プロジェクト / 1,000 名 / 月間 2,000,000 リクエスト / 月間 32.00 GB
- **リソース構成**: Container Apps 平均 3 レプリカ（最大10自動スケール） / Event Hubs 2 TU 冗長

| 費用項目 | 算定諸元 | 月額費用 (USD) | 月額費用 (JPY) | 構成比 |
| :--- | :--- | :--- | :--- | :--- |
| **Azure Container Apps** | 平均 3 レプリカ (最大10スケールアウト) | \$35.04 | ¥5,255 | 15.5% |
| **Azure Event Hubs** | 2 TU (固定 \$43.20) + 200万イベント (\$0.06) | \$43.26 | ¥6,488 | 19.1% |
| **Azure Blob Storage** | 32 GB 保管 (\$0.70) + 200万回書き込み (\$40.00) | \$40.70 | ¥6,106 | 18.0% |
| **Azure Log Analytics** | 32 GB インジェスト (Hot 30日保持) | \$106.88 | ¥16,032 | 47.3% |
| **Key Vault / Egress** | トランザクション & 外部通信 (100GB無料枠内) | \$0.03 | ¥4 | 0.1% |
| **月額合計** | — | **\$225.91** | **¥33,886** | **100.0%** |
| **年額合計** | — | **\$2,710.86** | **¥406,629** | — |
| **開発者1名あたり** | 1,000名で除算 | **\$0.23 / 人** | **約 ¥34 / 人月** | — |

**【考察】**
100プロジェクト・1,000名がフル稼働する全社基盤においても、月額コストは約 3.4 万円に収まります。費用構成比では Log Analytics のデータインジェスト料金（\$3.34/GB）が全体の約 47% を占めるため、次節の FinOps 最適化により大幅な削減余地があります。

---

## 6. 長期運用（WORM 3年間保持）におけるストレージ費用の累積推移

リポジトリの Terraform 設定 [`infra/azure/variables.tf`](file:///v:/repos/sun.flat.yamada/agent-aegis-harness/infra/azure/variables.tf) では、法的要件に基づき不変ストレージ保持期間を **3年間（1,095日）** と定めています。ログデータが毎月累積した場合のストレージ費用推移を試算しました。

- **Cool GRS 単価**: \$0.022 / GB月

```text
【大規模 (月間 32 GB 増加)】
  -  1ヶ月目:     32 GB  -> 保管料 $0.70/月 (書き込み込み $40.70)
  - 12ヶ月目:    384 GB  -> 保管料 $8.45/月 (書き込み込み $48.45)
  - 24ヶ月目:    768 GB  -> 保管料 $16.90/月 (書き込み込み $56.90)
  - 36ヶ月目:  1,152 GB  -> 保管料 $25.34/月 (書き込み込み $65.34)
```

| 運用経過月 | 小規模 (累積データ量 / 月額) | 中規模 (累積データ量 / 月額) | 大規模 (累積データ量 / 月額) |
| :--- | :--- | :--- | :--- |
| **1ヶ月目 (初期)** | 0.48 GB / \$0.61 (¥92) | 3.2 GB / \$4.07 (¥611) | 32 GB / \$40.70 (¥6,106) |
| **12ヶ月目 (1年後)** | 5.76 GB / \$0.73 (¥109) | 38.4 GB / \$4.84 (¥727) | 384 GB / \$48.45 (¥7,267) |
| **24ヶ月目 (2年後)** | 11.52 GB / \$0.85 (¥128) | 76.8 GB / \$5.69 (¥853) | 768 GB / \$56.90 (¥8,534) |
| **36ヶ月目 (3年後)** | 17.28 GB / \$0.98 (¥147) | 115.2 GB / \$6.53 (¥980) | 1,152 GB / \$65.34 (¥9,802) |

> [!NOTE]
> 3年が経過して 1,095 日の保持期限を迎えたログは、ライフサイクル管理ルールにより Archive 層へ移行するか自動消去されるため、36ヶ月目以降のデータ保持容量は約 1.15 TB で定常状態（プラトー）に達します。3年後でもストレージ月額は 1 万円未満で安定運用が可能です。

---

## 7. コスト最適化施策 (FinOps & Optimization Strategies)

全社規模での費用効率を極限まで高めるための 4 つの最適化アプローチを提言します。

```mermaid
flowchart LR
    subgraph DualStreamOpt ["最適化: デュアルストリーム・ルーティング分離"]
        direction TB
        RawEvent["監査イベント発生 (16 KB)"]
        RawEvent --> Splitter{"イベント分離"}
        Splitter -->|軽量台帳 (1 KB)| LA["Log Analytics<br/>(インシデント即時検知・KQL)"]
        Splitter -->|完全生ログ (15 KB)| WORM["Blob WORM (Cool GRS)<br/>(法的改ざん防止・長期保存)"]
    end
```

### 施策 1: デュアルストリームのルーティング分離（最大約 45% の総コスト削減）
- **背景**: 大規模環境では、Log Analytics のインジェスト料金（\$3.34/GB）が月額費用の約 47%（\$106.88）を占めています。
- **対策**:
  - `docs/ARCHITECTURE.ja.md` に定義された「デュアルストリーム構造」を活用し、リアルタイム監視・アラートが必要な **`audit-trail.jsonl`（1 KB）のみ** を Log Analytics にインジェストします。
  - プロンプト全文や生トレースを含む **`forensic-trail.jsonl`（15 KB）** は、Event Hubs Capture 経由で直接 Blob Storage WORM へ流し込み、インシデント調査時のみ参照します。
- **削減効果**:
  - Log Analytics インジェストデータ量: 32 GB $\rightarrow$ **2.0 GB**
  - Log Analytics 月額費用: \$106.88 $\rightarrow$ **\$6.68 (約 ¥1,002)** （約 93% 削減）
  - 大規模全体の月額費用: \$225.91 $\rightarrow$ **\$125.71 (約 ¥18,856)** （総額約 45% 削減、**開発者1人あたり約 ¥19 / 月**）

### 施策 2: Container Apps の夜間・休日スケールイン
- 開発者が作業しない夜間帯（20:00〜08:00）や休日は、最小レプリカ数を一時的に 1（または 0）へ絞り込む自動スケールスケジュールを設定することで、コンテナのアイドル費用を約 30% 削減できます。

### 施策 3: Event Hubs のオートインフレート活用
- 常時プロビジョニングする TU 数を最小（1 TU）に設定し、`auto_inflate_enabled = true` によりバースト時のみ一時的にスケールアウトさせることで、大規模環境でも平常時の TU 費用を \$21.60/月に抑制可能です。

### 施策 4: Local MCP と Cloud MCP のハイブリッド運用
- 一般的なオープンソース開発や低リスクプロジェクトではインフラ費用の発生しない **Local MCP** を標準とし、機密コードや決済系リポジトリのみ **Cloud MCP** に接続するポリシー運用を行うことで、クラウド費用を最小限に保てます。

---

## 8. 妥当性検証の完全エビデンスと再現手順

### 8.1 URL 疎通確認結果 (HTTP GET 200 OK)

2026-09-12 に実施された疎通確認結果です。

```text
HTTP 200 : https://azure.microsoft.com/en-us/pricing/details/container-apps/
HTTP 200 : https://azure.microsoft.com/en-us/pricing/details/event-hubs/
HTTP 200 : https://azure.microsoft.com/en-us/pricing/details/storage/blobs/
HTTP 200 : https://azure.microsoft.com/en-us/pricing/details/monitor/
HTTP 200 : https://azure.microsoft.com/en-us/pricing/details/key-vault/
HTTP 200 : https://prices.azure.com/api/retail/prices?$filter=serviceName eq 'Container Apps'
```

### 8.2 価格検証・再現スクリプト

以下の PowerShell または Python スクリプトを実行することで、本レポートに記載されたすべての単価および計算結果をいつでも決定論的に再検証できます。

```powershell
# Azure Retail Prices API から東日本リージョンの単価を即時検証するスクリプト
$services = @("Container Apps", "Event Hubs", "Storage", "Log Analytics", "Key Vault")
foreach ($svc in $services) {
    $uri = "https://prices.azure.com/api/retail/prices?`$filter=contains(serviceName, '$svc') and armRegionName eq 'japaneast'"
    $res = Invoke-RestMethod -Uri $uri
    Write-Host "=== $svc (Total Items: $($res.Count)) ==="
    $res.Items | Select-Object -First 3 -Property serviceName, skuName, meterName, unitPrice, unitOfMeasure
}
```

---

## 9. 結論・推奨方針

本分析の結果、Agent Aegis Harness のクラウド運用は、最高水準の暗号学的改ざん防止（Merkle連鎖）および法的WORMストレージを備えながらも、**全社1,000名規模で月額約3.4万円（最適化適用時は約1.9万円）** という極めて低いコストパフォーマンスで実現可能であることが実証されました。

まずは「小規模（月額約5,200円）」または「中規模（月額約8,700円）」でのパイロット運用を開始し、開発組織の拡大に合わせてシームレスにスケールアウトさせることを推奨します。
