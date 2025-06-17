import json
import os
import glob

def merge_reviews():
    # reviews_dataディレクトリ内のすべてのJSONファイルを取得
    json_files = glob.glob('reviews_data/*.json')
    
    # 結果を格納するリスト
    merged_data = []
    
    # 各JSONファイルを読み込んでマージ
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                merged_data.append(data)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # マージしたデータを新しいJSONファイルに書き込む
    with open('merged_reviews.json', 'w', encoding='utf-8') as outfile:
        json.dump(merged_data, outfile, ensure_ascii=False, indent=2)
    
    print(f"マージが完了しました。{len(merged_data)}件の大学データが merged_reviews.json に保存されました。")

if __name__ == "__main__":
    merge_reviews()
