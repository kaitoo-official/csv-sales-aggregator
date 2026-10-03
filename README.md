# csv-sales-aggregator

Aggregates multiple sales CSV files (UTF-8 / Shift_JIS) by store, month and product, with row-level error reporting and total verification. Python standard library only. All sample data is fictional.

---

複数の売上CSVをまとめて、**店舗別・月別・商品別**に集計するツールです。
**入力はすべて架空データ**です（実在の店舗・顧客のデータではありません）。

## できること
- フォルダ内のCSVをまとめて読み込む（UTF-8〈Excelの「CSV UTF-8」〉と Shift_JIS〈Excel標準のCSV〉の両方に対応）
- **元のCSVは変更しない**。結果は `output/実行日時/` に別ファイルで保存
- 必須列の不足、数値でない値、空欄、存在しない日付を、**ファイル名と行番号つきで報告**し、その行（列不足ならファイル）を集計から除外
- 「正常な入力行の金額合計」と「各集計の合計」が一致するかを自動で検証（OK／NG）
- 金額の `4,050` や `1800円` のような表記は数値として読み取る

## 入力の形式
必須列：`日付, 店舗, 商品, 数量, 金額`（列の順番は自由）

```csv
日付,店舗,商品,数量,金額
2026-09-01,渋谷店,ブレンドコーヒー,12,5400
2026/09/02,横浜店,ブレンドコーヒー,8,3600
```

## Windowsでの使い方
1. Python 3.9以上をインストール（https://www.python.org/ 。インストール時に「Add python.exe to PATH」にチェック）
2. このフォルダをエクスプローラーで開き、アドレスバーに `cmd` と入力して Enter
3. 次を実行：
```bat
py aggregate_sales.py --input sample_data --output output
```
- 自分のCSVで試す場合：CSVを入れたフォルダを `--input` に指定（例：`--input C:\Users\you\Desktop\売上CSV`）
- 出力先を入力フォルダの中にすると、元ファイル保護のためエラーで止まります

## 出力
`output/YYYYMMDD_HHMMSS/` に次の4ファイル（Excelでそのまま開けるUTF-8〈BOM付き〉）
| ファイル | 中身 |
|---|---|
| `集計_店舗別.csv` | 店舗ごとの数量・金額＋合計行 |
| `集計_月別.csv` | 月ごとの数量・金額＋合計行 |
| `集計_商品別.csv` | 商品ごとの数量・金額＋合計行 |
| `レポート.txt` | 読み込み件数、除外件数、問題点の一覧、合計の検証結果 |

出力例（`sample_data` の店舗別）：
```csv
店舗,数量,金額
大宮店,16,7800
横浜店,17,10450
渋谷店,59,30600
合計,92,48850
```

エラー報告の例（`sample_data_with_errors`）：
```
- 売上_新宿店_2026-09_列不足.csv: 必須列が不足しています → 数量（ファイルごと除外）
- 売上_池袋店_2026-09_不正な値あり.csv 3行目: 数量「三」が数値ではありません（行を除外）
- 売上_池袋店_2026-09_不正な値あり.csv 4行目: 金額「（空欄）」が数値ではありません（行を除外）
- 売上_池袋店_2026-09_不正な値あり.csv 5行目: 日付「2026-13-01」→ 日付の形式が不正（例：2026-09-01 または 2026/09/01）（行を除外）
```

## ファイル構成
```
├─ aggregate_sales.py          … 本体（標準ライブラリのみ）
├─ sample_data/                … 架空の正常データ4ファイル（うち1つはShift_JIS）
└─ sample_data_with_errors/    … 架空の不正データを含む3ファイル
```
実行すると `output/` に結果が作られます（リポジトリには含めていません）。

---
KAITOO Works の自主制作デモです。
