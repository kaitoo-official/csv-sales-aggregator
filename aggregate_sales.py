"""複数の売上CSVをまとめて集計する自主制作デモ（KAITOO Works）。

- 入力フォルダ内の *.csv をすべて読み込む（元ファイルは変更しない）
- 必須列の不足・不正な数値を行番号つきで報告し、その行は集計から除外する
- 店舗別・月別・商品別の集計を、出力フォルダ（実行日時ごと）に保存する
- 「正常な入力行の合計」と「集計結果の合計」が一致するかを検証する

標準ライブラリのみで動く（Python 3.9 以上）。
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

REQUIRED_COLUMNS = ["日付", "店舗", "商品", "数量", "金額"]
ENCODINGS = ["utf-8-sig", "cp932"]  # Excel保存のUTF-8（BOM付き）と Shift_JIS の両方に対応


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]], str]:
    last_error: Exception | None = None
    for enc in ENCODINGS:
        try:
            with path.open(encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                return [c.strip() for c in (reader.fieldnames or [])], rows, enc
        except UnicodeDecodeError as e:
            last_error = e
    raise ValueError(f"文字コードを判別できません（UTF-8 / Shift_JIS 以外の可能性）: {last_error}")


def parse_number(text: str) -> Decimal:
    cleaned = text.strip().replace(",", "").replace("円", "").replace("¥", "")
    if cleaned == "":
        raise InvalidOperation("空欄")
    return Decimal(cleaned)


def parse_month(text: str) -> str:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text.strip(), fmt).strftime("%Y-%m")
        except ValueError:
            pass
    raise ValueError("日付の形式が不正（例：2026-09-01 または 2026/09/01）")


def write_summary(path: Path, key_name: str, data: dict[str, list[Decimal]]) -> Decimal:
    total = Decimal(0)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([key_name, "数量", "金額"])
        for key in sorted(data):
            qty, amount = data[key]
            w.writerow([key, f"{qty:f}", f"{amount:f}"])
            total += amount
        w.writerow(["合計", f"{sum(v[0] for v in data.values()):f}", f"{total:f}"])
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="複数の売上CSVをまとめて集計します")
    parser.add_argument("--input", default="sample_data", help="入力CSVのフォルダ（既定：sample_data）")
    parser.add_argument("--output", default="output", help="出力先フォルダ（既定：output）")
    args = parser.parse_args()

    in_dir = Path(args.input)
    files = sorted(in_dir.glob("*.csv"))
    if not files:
        print(f"[エラー] 入力フォルダにCSVがありません: {in_dir.resolve()}")
        return 2

    out_dir = Path(args.output) / datetime.now().strftime("%Y%m%d_%H%M%S")
    if out_dir.resolve() == in_dir.resolve() or in_dir.resolve() in out_dir.resolve().parents:
        print("[エラー] 出力先を入力フォルダの中にしないでください（元ファイル保護のため）")
        return 2
    out_dir.mkdir(parents=True, exist_ok=False)

    by_store: dict[str, list[Decimal]] = defaultdict(lambda: [Decimal(0), Decimal(0)])
    by_month: dict[str, list[Decimal]] = defaultdict(lambda: [Decimal(0), Decimal(0)])
    by_product: dict[str, list[Decimal]] = defaultdict(lambda: [Decimal(0), Decimal(0)])
    problems: list[str] = []
    input_total = Decimal(0)
    ok_rows = 0
    total_rows = 0
    skipped_files: list[str] = []

    for path in files:
        try:
            columns, rows, enc = read_csv(path)
        except ValueError as e:
            problems.append(f"{path.name}: {e}（ファイルごと除外）")
            skipped_files.append(path.name)
            continue
        missing = [c for c in REQUIRED_COLUMNS if c not in columns]
        if missing:
            problems.append(f"{path.name}: 必須列が不足しています → {', '.join(missing)}（ファイルごと除外）")
            skipped_files.append(path.name)
            continue
        for i, row in enumerate(rows, start=2):  # 1行目は見出し
            total_rows += 1
            where = f"{path.name} {i}行目"
            try:
                month = parse_month(row["日付"] or "")
            except ValueError as e:
                problems.append(f"{where}: 日付「{row['日付']}」→ {e}（行を除外）")
                continue
            store = (row["店舗"] or "").strip()
            product = (row["商品"] or "").strip()
            if not store or not product:
                problems.append(f"{where}: 店舗または商品が空欄です（行を除外）")
                continue
            bad = []
            values = {}
            for col in ("数量", "金額"):
                try:
                    values[col] = parse_number(row[col] or "")
                except InvalidOperation:
                    bad.append(f"{col}「{row[col] or '（空欄）'}」")
            if bad:
                problems.append(f"{where}: {'・'.join(bad)}が数値ではありません（行を除外）")
                continue
            qty, amount = values["数量"], values["金額"]
            for bucket, key in ((by_store, store), (by_month, month), (by_product, product)):
                bucket[key][0] += qty
                bucket[key][1] += amount
            input_total += amount
            ok_rows += 1

    totals = {
        "店舗別": write_summary(out_dir / "集計_店舗別.csv", "店舗", by_store),
        "月別": write_summary(out_dir / "集計_月別.csv", "月", by_month),
        "商品別": write_summary(out_dir / "集計_商品別.csv", "商品", by_product),
    }
    all_match = all(t == input_total for t in totals.values())

    lines = [
        "売上CSV集計レポート（KAITOO Works 自主制作デモ）",
        f"実行日時: {datetime.now():%Y-%m-%d %H:%M:%S}",
        f"入力フォルダ: {in_dir.resolve()}",
        f"読み込んだファイル: {len(files)}件（除外 {len(skipped_files)}件）",
        f"データ行: {total_rows}行 → 集計 {ok_rows}行／除外 {total_rows - ok_rows}行",
        f"正常な入力行の金額合計: {input_total:f}",
        *[f"{k}の合計: {v:f}" for k, v in totals.items()],
        f"検証（入力合計と各集計の合計が一致）: {'OK' if all_match else 'NG：一致しません'}",
        "",
        f"問題点: {len(problems)}件",
        *[f"- {p}" for p in problems],
    ]
    (out_dir / "レポート.txt").write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    print("\n".join(lines))
    print(f"\n出力先: {out_dir.resolve()}")
    return 0 if all_match else 1


if __name__ == "__main__":
    sys.exit(main())
