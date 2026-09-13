"""
VS Code GitHub Copilot Chat Delta Session JSONL Parser & Replay Engine
Parses streaming delta records (kind 0: base, kind 1: set, kind 2: append)
from VS Code workspaceStorage/chatSessions/*.jsonl and converts them to NormalizedAIEvent.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from aegis.models import (
    ClientToolType,
    ForensicProvenance,
    NormalizedAIEvent,
    NormalizedInference,
    NormalizedToolCall,
    NormalizedTrigger,
    TriggerSourceType,
)
from aegis.sentinel.redactor import SensitiveRedactor


class CopilotDeltaSessionParser:
    """VS Code GitHub Copilot Chat セッションの差分ストリーム再生 & 監査イベント抽出パーサー"""

    def __init__(self):
        self.redactor = SensitiveRedactor()

    def parse_session_file(self, file_path: Path) -> List[NormalizedAIEvent]:
        """
        JSONL ファイルを読み込み、Kind 0/1/2 のデルタストリームを再生して完全なセッション状態を復元、
        NormalizedAIEvent のリストへ変換・返却する。
        """
        events: List[NormalizedAIEvent] = []
        if not file_path.exists() or not file_path.is_file():
            return events

        # 元ファイルの完全性ダイジェスト (SHA-256) を計算
        try:
            raw_bytes = file_path.read_bytes()
            if not raw_bytes:
                return events
            file_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        except Exception:
            return events

        # デルタストリームのリプレイ
        replayed_state = self._replay_delta_stream(raw_bytes.decode("utf-8", errors="ignore"))
        if not replayed_state:
            return events

        session_id = replayed_state.get("sessionId") or file_path.stem

        # requests から各ターンのイベントを抽出
        requests = replayed_state.get("requests", [])
        if not isinstance(requests, list):
            requests = []

        # requests が空の場合でもセッション全体のメタ情報があれば1件生成
        if not requests:
            event = self._build_session_summary_event(replayed_state, file_path, file_sha256, session_id)
            if event:
                events.append(event)
            return events

        for idx, req in enumerate(requests):
            if not isinstance(req, dict):
                continue
            event = self._normalize_turn(
                req=req,
                replayed_state=replayed_state,
                turn_index=idx,
                file_path=file_path,
                file_sha256=file_sha256,
                session_id=session_id
            )
            if event:
                events.append(event)

        return events

    def _replay_delta_stream(self, content: str) -> Dict[str, Any]:
        """
        VS Code Delta JSONL 形式を行ごとに適用してオブジェクト状態を再構築する。
        Kind 0: スナップショット初期化
        Kind 1: プロパティ設定 (パス k に従って値をセット)
        Kind 2: 配列追加 (パス k に従って要素を追加)
        """
        state: Dict[str, Any] = {}

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except Exception:
                continue

            if not isinstance(record, dict):
                continue

            kind = record.get("kind")
            val = record.get("v")
            keys = record.get("k")

            if kind == 0:
                # 初期状態
                if isinstance(val, dict):
                    state = val
            elif kind == 1 and keys is not None:
                # プロパティ設定
                self._apply_set_delta(state, keys, val)
            elif kind == 2 and keys is not None:
                # 配列追加
                self._apply_append_delta(state, keys, val)

        return state

    def _apply_set_delta(self, target: Any, path: List[Union[str, int]], value: Any):
        """指定パスのキーに値を設定"""
        if not path:
            return
        curr = target
        for i, p in enumerate(path[:-1]):
            nxt = path[i + 1]
            if isinstance(p, int):
                while len(curr) <= p:
                    curr.append({} if isinstance(nxt, str) else [])
                curr = curr[p]
            else:
                if p not in curr:
                    curr[p] = {} if isinstance(nxt, str) else []
                curr = curr[p]
        last_key = path[-1]
        if isinstance(last_key, int):
            while len(curr) <= last_key:
                curr.append(None)
            curr[last_key] = value
        else:
            if isinstance(curr, dict):
                curr[last_key] = value

    def _apply_append_delta(self, target: Any, path: List[Union[str, int]], value: Any):
        """指定パスの配列に要素を追加"""
        if not path:
            return
        curr = target
        for i, p in enumerate(path):
            if isinstance(p, int):
                while len(curr) <= p:
                    curr.append({})
                curr = curr[p]
            else:
                if p not in curr:
                    curr[p] = []
                curr = curr[p]

        if isinstance(curr, list):
            if isinstance(value, list):
                curr.extend(value)
            else:
                curr.append(value)

    def _extract_prompt_text(self, message_obj: Any) -> str:
        """message オブジェクトからユーザープロンプト文字列を抽出"""
        if isinstance(message_obj, str):
            return message_obj
        if isinstance(message_obj, dict):
            if "text" in message_obj:
                return str(message_obj["text"])
            if "parts" in message_obj:
                parts = message_obj["parts"]
                if isinstance(parts, list):
                    texts = [p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p]
                    if texts:
                        return " ".join(texts)
            return json.dumps(message_obj, ensure_ascii=False)
        return ""

    def _extract_files_and_tools(self, response_items: Any, content_refs: Any) -> Tuple[List[str], List[NormalizedToolCall], str]:
        """レスポンス要素および参照から言及ファイル、ツール呼出、アシスタント要約を抽出"""
        affected_files: List[str] = []
        tool_calls: List[NormalizedToolCall] = []
        response_texts: List[str] = []

        # 1. 参照ファイル (contentReferences)
        if isinstance(content_refs, list):
            for ref in content_refs:
                if isinstance(ref, dict):
                    uri = ref.get("reference") or ref.get("uri") or ref.get("path")
                    if isinstance(uri, dict) and "path" in uri:
                        affected_files.append(str(uri["path"]))
                    elif isinstance(uri, str):
                        affected_files.append(uri)

        # 2. レスポンスブロック (response)
        if isinstance(response_items, list):
            for item in response_items:
                if isinstance(item, dict):
                    # テキスト値
                    if "value" in item:
                        txt = str(item["value"])
                        response_texts.append(txt)
                        # ファイルパスの検出ヒューリスティック (例: `file.py` や path/to/file)
                        for word in txt.split():
                            clean_word = word.strip("`'\"(),:;")
                            if any(clean_word.endswith(ext) for ext in [".py", ".ts", ".js", ".json", ".md", ".yaml", ".yml", ".go", ".rs", ".html"]):
                                affected_files.append(clean_word)
                    # インライン参照
                    if item.get("kind") == "inlineReference":
                        ref = item.get("inlineReference", {})
                        if isinstance(ref, dict) and "path" in ref:
                            affected_files.append(str(ref["path"]))
                    # ツール呼出
                    if "toolUse" in item or "tool" in item:
                        t = item.get("toolUse") or item.get("tool")
                        if isinstance(t, dict):
                            tool_calls.append(
                                NormalizedToolCall(
                                    tool_name=t.get("name", "copilot_tool"),
                                    arguments=t.get("input") or t.get("parameters") or {},
                                    status="SUCCESS"
                                )
                            )
                    # Agent呼出
                    if item.get("agent"):
                        ag = item.get("agent")
                        if isinstance(ag, dict):
                            tool_calls.append(
                                NormalizedToolCall(
                                    tool_name=ag.get("id", "agent_invocation"),
                                    arguments={"agent_name": ag.get("extensionDisplayName", "copilot_agent")},
                                    status="SUCCESS"
                                )
                            )

        summary_text = " ".join(response_texts)[:1000] if response_texts else ""
        # 重複除去
        unique_files = list(dict.fromkeys([f for f in affected_files if f and not f.startswith("http")]))
        return unique_files, tool_calls, summary_text

    def _normalize_turn(
        self,
        req: Dict[str, Any],
        replayed_state: Dict[str, Any],
        turn_index: int,
        file_path: Path,
        file_sha256: str,
        session_id: str
    ) -> Optional[NormalizedAIEvent]:
        """単一のリクエストターンを NormalizedAIEvent に変換"""
        raw_msg = self._extract_prompt_text(req.get("message"))
        sanitized_prompt, _ = self.redactor.redact_text(raw_msg or f"[Copilot Turn {turn_index}]")

        # タイムスタンプ取得 (ミリ秒 -> datetime)
        ts_ms = req.get("timestamp") or replayed_state.get("creationDate")
        if isinstance(ts_ms, (int, float)):
            try:
                event_time = datetime.utcfromtimestamp(ts_ms / 1000.0)
            except Exception:
                event_time = datetime.utcnow()
        else:
            event_time = datetime.utcnow()

        # レスポンス及び参照ファイル
        response_items = req.get("response", [])
        content_refs = req.get("contentReferences", [])
        affected_files, tool_calls, resp_summary = self._extract_files_and_tools(response_items, content_refs)

        # モデル名・エージェント名
        agent_info = req.get("agent", {})
        agent_id = agent_info.get("id") if isinstance(agent_info, dict) else "copilot"
        model_id = req.get("modelId")
        if not model_id and isinstance(replayed_state.get("inputState"), dict):
            sel_model = replayed_state["inputState"].get("selectedModel", {})
            if isinstance(sel_model, dict):
                model_id = sel_model.get("identifier") or sel_model.get("id")

        model_name = f"copilot/{model_id}" if model_id else "github-copilot"

        # フォレンジクス諸元モデル
        provenance = ForensicProvenance(
            source_path=str(file_path.resolve()),
            source_sha256=file_sha256,
            parser_id="copilot-delta-v1",
            extraction_timestamp=datetime.utcnow(),
            confidence_level="HIGH",
            raw_record_kind=req.get("kind")
        )

        tags = [
            "source:github-copilot",
            "extraction:retroactive",
            "storage:vscode-workspace-storage",
            f"session:{session_id}",
            f"agent:{agent_id}"
        ]

        return NormalizedAIEvent(
            trace_id=f"{session_id}_turn_{turn_index}",
            timestamp=event_time,
            client_tool=ClientToolType.COPILOT,
            extraction_method="retro_local_discovery",
            tags=tags,
            forensic_provenance=provenance,
            trigger=NormalizedTrigger(
                source=TriggerSourceType.CHAT_PROMPT,
                raw_prompt=None,  # シークレット保護のため raw は記録しない
                sanitized_prompt=sanitized_prompt,
                user_identity="local-copilot-user",
                session_id=session_id
            ),
            inference=NormalizedInference(
                model_name=model_name,
                chain_of_thought_summary=resp_summary[:500] if resp_summary else None,
                user_intent_summary=sanitized_prompt[:200]
            ),
            tool_calls=tool_calls,
            affected_files=affected_files,
            sentinel_verdict_status="ALLOW"
        )

    def _build_session_summary_event(
        self,
        replayed_state: Dict[str, Any],
        file_path: Path,
        file_sha256: str,
        session_id: str
    ) -> Optional[NormalizedAIEvent]:
        """リクエストが空のセッション初期状態からサマリエントリを生成"""
        title = replayed_state.get("customTitle") or replayed_state.get("title") or "Empty Copilot Session"
        ts_ms = replayed_state.get("creationDate")
        if isinstance(ts_ms, (int, float)):
            try:
                event_time = datetime.utcfromtimestamp(ts_ms / 1000.0)
            except Exception:
                event_time = datetime.utcnow()
        else:
            event_time = datetime.utcnow()

        provenance = ForensicProvenance(
            source_path=str(file_path.resolve()),
            source_sha256=file_sha256,
            parser_id="copilot-delta-v1",
            extraction_timestamp=datetime.utcnow(),
            confidence_level="MEDIUM"
        )

        return NormalizedAIEvent(
            trace_id=session_id,
            timestamp=event_time,
            client_tool=ClientToolType.COPILOT,
            extraction_method="retro_local_discovery",
            tags=["source:github-copilot", "extraction:retroactive", f"session:{session_id}"],
            forensic_provenance=provenance,
            trigger=NormalizedTrigger(
                source=TriggerSourceType.CHAT_PROMPT,
                sanitized_prompt=f"[Session Initialized: {title}]",
                user_identity="local-copilot-user",
                session_id=session_id
            ),
            sentinel_verdict_status="ALLOW"
        )
