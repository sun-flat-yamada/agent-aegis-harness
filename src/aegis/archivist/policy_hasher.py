"""
Policy Hasher for Agent Aegis Harness
Computes deterministic SHA-256 digest of rules, skills, and configuration bundles
"""
import hashlib
import os
from pathlib import Path
from typing import List, Union

class PolicyHasher:
    def __init__(self, target_dirs: Union[str, List[str]] = None):
        if target_dirs is None:
            self.target_dirs = [".aegis/rules", ".skills"]
        elif isinstance(target_dirs, str):
            self.target_dirs = [target_dirs]
        else:
            self.target_dirs = list(target_dirs)

    def compute_file_hash(self, file_path: Union[str, Path]) -> str:
        """単一ファイルの正規化 SHA-256 ハッシュを計算 (改行コード LF 正規化)"""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(path, "rb") as f:
            content = f.read()
            # 改行コードを LF (\n) に正規化して OS 間の差異を排除
            normalized = content.replace(b"\r\n", b"\n")
            return hashlib.sha256(normalized).hexdigest()

    def list_target_files(self) -> List[Path]:
        """対象ディレクトリ内のすべての設定・ポリシーファイルを決定論的にソートして取得"""
        files: List[Path] = []
        for dir_path_str in self.target_dirs:
            dir_path = Path(dir_path_str)
            if not dir_path.exists():
                continue
            for root, _, filenames in os.walk(dir_path):
                for filename in filenames:
                    if filename.endswith((".yaml", ".yml", ".json", ".md")):
                        files.append(Path(root) / filename)
        
        # OS 非依存で決定論的なソートを行う (POSIX 相対パス基準)
        return sorted(files, key=lambda p: p.as_posix())

    def compute_digest(self) -> str:
        """
        すべての対象ファイルの (相対パス + ファイルハッシュ) を結合し、
        ポリシーバンドルの決定論的 SHA-256 ダイジェストを算出する。
        """
        files = self.list_target_files()
        if not files:
            # 対象ファイルが存在しない場合のデフォルトハッシュ
            return "sha256:" + hashlib.sha256(b"EMPTY_POLICY_BUNDLE").hexdigest()

        hasher = hashlib.sha256()
        for file_path in files:
            posix_rel_path = file_path.as_posix()
            file_hash = self.compute_file_hash(file_path)
            entry = f"{posix_rel_path}:{file_hash}\n"
            hasher.update(entry.encode("utf-8"))

        return f"sha256:{hasher.hexdigest()}"
