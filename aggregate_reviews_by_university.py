import json
import os

def aggregate_reviews_by_university():
    """
    merged_reviews.jsonから大学別に口コミを統合するプログラム
    各大学の口コミ文章（review_content）を抽出して、大学ごとにまとめます
    """
    print("大学別口コミ統合処理を開始します...")
    
    # merged_reviews.jsonからデータを読み込む
    try:
        with open('merged_reviews.json', 'r', encoding='utf-8') as file:
            merged_data = json.load(file)
            print(f"{len(merged_data)}件の大学データを読み込みました")
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
        return
    
    # 大学別に口コミを統合するための辞書
    university_reviews = {}
    
    # 各大学のデータを処理
    for university_data in merged_data:
        university_name = university_data.get('university_name', 'Unknown')
        reviews = university_data.get('reviews', [])
        
        # この大学の口コミテキストを格納するセット（重複を排除するため）
        review_texts_set = set()
        
        # 各口コミから全ての文章を抽出
        for review in reviews:
            # 抽出する詳細情報のフィールド
            detail_fields = [
                'review_content',
                'overall_rating_detail',
                '講義・授業_detail',
                'laboratory_seminar_detail',
                'career_detail',
                'access_location_detail',
                'facilities_detail',
                'friendship_romance_detail',
                'student_life_detail',
                'department_curriculum_detail',
                'gender_ratio_detail',
                'motivation_detail',
                'career_path_detail'
            ]
            
            # 各フィールドの値を抽出
            for field in detail_fields:
                text = review.get(field, '')
                if text and text.strip():
                    review_texts_set.add(text.strip())
        
        # セットをリストに変換
        review_texts = list(review_texts_set)
        
        # 大学名をキーとして口コミを辞書に追加
        if university_name not in university_reviews:
            university_reviews[university_name] = []
        
        university_reviews[university_name].extend(review_texts)
        
        print(f"{university_name}: {len(review_texts)}件の口コミを統合しました")
    
    # 結果を整形
    result = [
        {
            "university_name": university_name,
            "reviews": reviews
        }
        for university_name, reviews in university_reviews.items()
    ]
    
    # 統合したデータを新しいJSONファイルに保存
    output_file = 'aggregated_reviews_by_university.json'
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(result, outfile, ensure_ascii=False, indent=2)
    
    print(f"処理が完了しました。{len(result)}件の大学データが {output_file} に保存されました。")
    print(f"合計口コミ数: {sum(len(univ['reviews']) for univ in result)}件")

if __name__ == "__main__":
    aggregate_reviews_by_university()
