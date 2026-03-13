#!/usr/bin/env python3
"""
Local CSV anonymizer with optional Ollama-assisted text anonymization.

Features:
- Rule-based anonymization for common PII columns (name/email/phone/id/address).
- Optional LLM anonymization for selected free-text columns via local Ollama.
- Deterministic output: same input value -> same anonymized value in one run.

Usage:
  python scripts/anonymize_csv_with_ollama.py \
    --input data/raw.csv \
    --output data/anonymized.csv

  python scripts/anonymize_csv_with_ollama.py \
    --input data/raw.csv \
    --output data/anonymized.csv \
    --llm-columns notes,comment \
    --model llama3:8b
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple


SENSITIVE_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"email|e-mail|mail", re.I)),
    ("phone", re.compile(r"phone|mobile|tel|contact", re.I)),
    ("name", re.compile(r"name|full_name|firstname|lastname|realname", re.I)),
    ("id", re.compile(r"\b(id|uid|user_id|身份证|passport|ssn|tax)\b", re.I)),
    ("address", re.compile(r"address|addr|location|street|city|province", re.I)),
]


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[\d\s\-()]{7,}$")


@dataclass
class Anonymizer:
    model: str
    ollama_url: str
    llm_columns: set[str] = field(default_factory=set)
    # cache[(kind, original)] = anonymized
    cache: Dict[Tuple[str, str], str] = field(default_factory=dict)

    def anonymize_cell(self, column: str, value: str) -> str:
        if value is None:
            return value
        original = value.strip()
        if original == "":
            return value

        if column.lower() in self.llm_columns:
            return self._cached("llm", original, self._llm_anonymize_text)

        kind = self._infer_kind(column, original)
        if kind == "email":
            return self._cached("email", original, self._anon_email)
        if kind == "phone":
            return self._cached("phone", original, self._anon_phone)
        if kind == "name":
            return self._cached("name", original, self._anon_name)
        if kind == "id":
            return self._cached("id", original, self._anon_id)
        if kind == "address":
            return self._cached("address", original, self._anon_address)
        return value

    def _infer_kind(self, column: str, value: str) -> Optional[str]:
        lowered = column.lower()
        for kind, pattern in SENSITIVE_PATTERNS:
            if pattern.search(lowered):
                return kind

        # weak content-based fallback
        if EMAIL_RE.match(value):
            return "email"
        if PHONE_RE.match(value):
            return "phone"
        return None

    def _cached(self, kind: str, original: str, func):
        key = (kind, original)
        if key not in self.cache:
            self.cache[key] = func(original)
        return self.cache[key]

    def _short_hash(self, text: str, length: int = 10) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]

    def _anon_email(self, email: str) -> str:
        # Keep deterministic pseudonym and fixed safe domain.
        return f"user_{self._short_hash(email, 12)}@example.com"

    def _anon_phone(self, phone: str) -> str:
        digits = re.sub(r"\D", "", phone)
        if not digits:
            return f"PHONE_{self._short_hash(phone, 8)}"
        hashed = self._short_hash(phone, len(digits))
        mapped = "".join(str(int(ch, 16) % 10) for ch in hashed)
        return f"+{mapped}" if phone.strip().startswith("+") else mapped

    def _anon_name(self, name: str) -> str:
        return f"PERSON_{self._short_hash(name, 8)}"

    def _anon_id(self, value: str) -> str:
        return f"ID_{self._short_hash(value, 12)}"

    def _anon_address(self, value: str) -> str:
        return f"ADDRESS_{self._short_hash(value, 10)}"

    def _llm_anonymize_text(self, text: str) -> str:
        prompt = (
            "你是数据脱敏助手。请将下面文本中的个人敏感信息匿名化，"
            "包括姓名、手机号、邮箱、身份证号、住址、银行卡号等。"
            "要求：保留原文语言和语义，不要添加解释，只输出脱敏后的文本。\n\n"
            f"原文：{text}"
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0,
            },
        }

        req = urllib.request.Request(
            self.ollama_url.rstrip("/") + "/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "无法访问 Ollama API。请确认已启动 Ollama 并且模型可用。"
                f" 当前地址: {self.ollama_url}"
            ) from exc

        result = body.get("response", "")
        return result.strip() if result else text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Anonymize a CSV locally with optional Ollama support.")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument(
        "--llm-columns",
        default="",
        help="Comma-separated column names that should be anonymized by Ollama (for free text).",
    )
    parser.add_argument("--model", default="llama3:8b", help="Ollama model name")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434", help="Ollama base URL")
    parser.add_argument("--encoding", default="utf-8", help="CSV encoding")
    parser.add_argument("--delimiter", default=",", help="CSV delimiter")
    return parser.parse_args()


def normalize_columns(columns_raw: str) -> set[str]:
    if not columns_raw.strip():
        return set()
    return {c.strip().lower() for c in columns_raw.split(",") if c.strip()}


def process_csv(
    input_path: str,
    output_path: str,
    encoding: str,
    delimiter: str,
    anonymizer: Anonymizer,
) -> None:
    with open(input_path, "r", encoding=encoding, newline="") as f_in:
        reader = csv.DictReader(f_in, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("CSV 缺少表头（header）")

        with open(output_path, "w", encoding=encoding, newline="") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames, delimiter=delimiter)
            writer.writeheader()

            for row in reader:
                out_row = {}
                for col in reader.fieldnames:
                    val = row.get(col, "")
                    out_row[col] = anonymizer.anonymize_cell(col, val)
                writer.writerow(out_row)


def main() -> None:
    args = parse_args()
    llm_columns = normalize_columns(args.llm_columns)

    anonymizer = Anonymizer(
        model=args.model,
        ollama_url=args.ollama_url,
        llm_columns=llm_columns,
    )

    process_csv(
        input_path=args.input,
        output_path=args.output,
        encoding=args.encoding,
        delimiter=args.delimiter,
        anonymizer=anonymizer,
    )

    print("匿名化完成")
    print(f"输入: {args.input}")
    print(f"输出: {args.output}")
    if llm_columns:
        print(f"LLM 列: {', '.join(sorted(llm_columns))}")


if __name__ == "__main__":
    main()
