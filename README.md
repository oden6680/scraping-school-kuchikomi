# 大学口コミスクレイピングツール

このツールは、[みんなの大学情報](https://www.minkou.jp/university/)サイトから大学の口コミ情報を収集するための Python スクリプトです。

## 機能

- URL リストから複数の大学ページの口コミ情報を自動収集
- 大学名、投稿日、投稿者情報、口コミ内容、評価項目などを抽出
- 収集したデータを JSON 形式と CSV 形式で保存
- サーバー負荷を考慮した遅延機能
- ページング機能により最大 100 件の口コミを取得可能

## 必要環境

- Python 3.6 以上
- 必要なライブラリ（requirements.txt に記載）

## インストール方法

1. リポジトリをクローンまたはダウンロードします
2. 必要なライブラリをインストールします

```bash
pip install -r requirements.txt
```

## 使用方法

1. `urlList.json`ファイルに、スクレイピングしたい大学の URL を配列形式で記載します

   ```json
   ["https://www.minkou.jp/university/school/xxxxx/", "https://www.minkou.jp/university/school/yyyyy/"]
   ```

2. スクリプトを実行します

   ```bash
   # 通常実行（urlList.jsonの全URLを使用）
   python scrape_reviews.py

   # テストモード（test_urls.jsonの少数URLのみ使用）
   python scrape_reviews.py --test

   # 遅延時間を変更（秒）
   python scrape_reviews.py --delay 5

   # 出力ディレクトリを変更
   python scrape_reviews.py --output my_data

   # CSVファイルも出力する（デフォルトはJSONのみ）
   python scrape_reviews.py --csv

   # 最大取得口コミ数を指定（デフォルト: 20件）
   python scrape_reviews.py --max-reviews 100

   # 複数オプションの組み合わせ
   python scrape_reviews.py --test --delay 1 --output test_data --csv --max-reviews 50
   ```

3. スクレイピングが完了すると、指定した出力ディレクトリ（デフォルトは`reviews_data`）に結果が保存されます

## 出力ファイル

スクレイピング結果は以下の形式で保存されます：

1. **JSON ファイル** (デフォルト): 各大学ごとに個別の JSON ファイルが作成されます

   - ファイル名: `大学名_YYYYMMDD_HHMMSS.json`
   - 形式: 大学名、URL、口コミ情報の配列

2. **CSV ファイル** (オプション): `--csv`オプションを指定した場合のみ出力されます
   - ファイル名: `university_reviews_YYYYMMDD_HHMMSS.csv`
   - 列: University, URL, Date, Review

## 注意事項

- 過度なリクエストはサーバーに負荷をかける可能性があるため、`delay_seconds`の値を適切に設定してください
- スクレイピングは対象サイトの利用規約に従って行ってください
- サイトの構造が変更された場合、スクリプトが正常に動作しなくなる可能性があります
- 商用利用については、対象サイトの規約を確認してください

## コマンドラインオプション

スクリプトは以下のコマンドラインオプションをサポートしています：

| オプション        | 説明                                                                                                                            |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `--test`          | テストモードで実行します。`test_urls.json`の少数 URL のみを使用します。                                                         |
| `--delay SECONDS` | リクエスト間の遅延時間を秒単位で指定します（デフォルト: 3.0 秒）。                                                              |
| `--output DIR`    | 結果を保存するディレクトリを指定します（デフォルト: reviews_data）。                                                            |
| `--csv`           | CSV ファイルも出力します（デフォルトは JSON のみ）。                                                                            |
| `--max-reviews N` | 1 大学あたりの最大取得口コミ数を指定します（デフォルト: 20 件）。例えば、`--max-reviews 100`で最大 100 件の口コミを取得します。 |

## 開発とテスト

開発やテスト時には、`--test`オプションを使用することで、少数の URL だけを対象にスクレイピングを実行できます。これにより、スクリプトの動作確認を素早く行うことができます。

```bash
# テストモードで実行（遅延時間を1秒に短縮）
python scrape_reviews.py --test --delay 1
```

テスト用の URL は`test_urls.json`ファイルに記載されています。必要に応じてこのファイルを編集してください。

## ページング機能

このスクリプトはページング機能を備えており、複数ページにわたる口コミ情報を取得できます。デフォルトでは 1 大学あたり 20 件の口コミを取得しますが、`--max-reviews`オプションを使用することで、最大取得件数を変更できます。

例えば、以下のコマンドで 1 大学あたり最大 100 件の口コミを取得できます：

```bash
python scrape_reviews.py --max-reviews 100
```

各ページには約 10 件の口コミが含まれているため、100 件の口コミを取得するには約 10 ページ分のデータを取得することになります。
