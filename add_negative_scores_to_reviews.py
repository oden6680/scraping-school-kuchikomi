import json
import os
import sys
import argparse
from janome.tokenizer import Tokenizer
from gensim.models import KeyedVectors
from gensim.models.fasttext import load_facebook_model
import numpy as np
from tqdm import tqdm

def add_negative_scores_to_reviews(input_file, output_file, model_path):
    """
    merged_reviews.jsonの各口コミにネガティブスコアを追加する
    
    Args:
        input_file (str): 入力JSONファイルのパス（merged_reviews.json）
        output_file (str): 出力JSONファイルのパス
        model_path (str): fastTextモデルのパス
    """
    print("口コミごとのネガティブスコア計算を開始します...")
    
    # JSONデータの読み込み
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"{len(data)}件の大学データを読み込みました")
    except Exception as e:
        print(f"データ読み込みエラー: {e}")
        return
    
    # 事前学習済み fastText 日本語ベクトルのロード
    try:
        print(f"fastTextモデルを読み込んでいます: {model_path}")
        # fastTextモデルの読み込み方法
        try:
            # まずFacebookのfastTextモデルとして読み込みを試みる
            model = load_facebook_model(model_path)
            model = model.wv  # word vectorsを取得
        except Exception as e1:
            print(f"Facebookモデルとしての読み込みに失敗しました: {e1}")
            try:
                # 次にWord2Vecフォーマットとして読み込みを試みる
                model = KeyedVectors.load_word2vec_format(model_path, binary=True, encoding='utf-8', unicode_errors='ignore')
            except Exception as e2:
                print(f"Word2Vecフォーマットとしての読み込みに失敗しました: {e2}")
                # 最後にバイナリエンコーディングを変えて試みる
                model = KeyedVectors.load_word2vec_format(model_path, binary=True, encoding='latin1')
        
        print("モデルの読み込みが完了しました")
        
        # 「良い」⇔「悪い」軸ベクトルを定義
        axis = model['悪い'] - model['良い']  # 悪い方向がポジティブになるように
        print("感情分析の軸ベクトルを定義しました")
    except Exception as e:
        print(f"モデル読み込みエラー: {e}")
        return
    
    # 形態素解析器の初期化
    tokenizer = Tokenizer()
    
    # 各大学の各口コミにネガティブスコアを追加
    total_reviews = sum(len(uni['reviews']) for uni in data)
    processed_reviews = 0
    
    for uni_idx, uni in enumerate(data):
        university_name = uni['university_name']
        print(f"[{uni_idx+1}/{len(data)}] {university_name}の口コミを処理中...")
        
        for review in tqdm(uni['reviews'], desc=f"{university_name}の口コミ処理"):
            # 口コミのテキストを取得（複数のフィールドを結合）
            review_text = ""
            text_fields = [
                'review_content', 'overall_rating_detail',
                '講義・授業_detail', 'laboratory_seminar_detail', 'career_detail',
                'access_location_detail', 'facilities_detail', 'friendship_romance_detail',
                'student_life_detail', 'department_curriculum_detail', 'gender_ratio_detail',
                'motivation_detail', 'career_path_detail'
            ]
            
            for field in text_fields:
                if field in review and review[field]:
                    review_text += review[field] + " "
            
            if not review_text.strip():  # テキストが空の場合はスキップ
                review['negative_score'] = 0.0
                processed_reviews += 1
                continue
            
            # 1) 形態素解析して単語リスト
            tokens = [t.surface for t in tokenizer.tokenize(review_text) if t.part_of_speech.startswith('名詞,一般')]
            
            # 2) レビュー全体のベクトルを平均ベクトルで近似
            vecs = []
            for w in tokens:
                if w in model:
                    vecs.append(model[w])
            
            # 3) ネガティブスコアを計算
            if vecs:
                review_vec = np.mean(vecs, axis=0)
                # ベクトルのノルムが0でないことを確認
                review_norm = np.linalg.norm(review_vec)
                axis_norm = np.linalg.norm(axis)
                if review_norm > 0 and axis_norm > 0:
                    # ネガティブ度合い = cos(review_vec, axis)
                    neg = np.dot(review_vec, axis) / (review_norm * axis_norm)
                else:
                    neg = 0.0
            else:
                neg = 0.0
            
            # 4) 口コミにネガティブスコアを追加
            review['negative_score'] = float(neg)
            processed_reviews += 1
        
        print(f"{university_name}の口コミ処理が完了しました。進捗: {processed_reviews}/{total_reviews}")
    
    # 更新したデータを保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"処理が完了しました。{processed_reviews}件の口コミにネガティブスコアを追加しました。")
    print(f"結果は {output_file} に保存されました。")
    return data

if __name__ == "__main__":
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='merged_reviews.jsonの各口コミにネガティブスコアを追加する')
    parser.add_argument('--input', '-i', default='merged_reviews.json',
                        help='入力JSONファイルのパス（デフォルト: merged_reviews.json）')
    parser.add_argument('--output', '-o', default='merged_reviews_with_scores.json',
                        help='出力JSONファイルのパス（デフォルト: merged_reviews_with_scores.json）')
    parser.add_argument('--model', '-m', default='cc.ja.300.bin',
                        help='fastTextモデルのパス（デフォルト: cc.ja.300.bin）')
    
    args = parser.parse_args()
    
    # 入力ファイルの存在確認
    if not os.path.exists(args.input):
        print(f"エラー: 入力ファイルが見つかりません: {args.input}")
        sys.exit(1)
    
    # モデルファイルの存在確認
    if not os.path.exists(args.model):
        print(f"エラー: モデルファイルが見つかりません: {args.model}")
        print("fastTextモデルが必要です。analyze_university_reviews.py --download を実行してダウンロードしてください。")
        sys.exit(1)
    
    # 処理の実行
    add_negative_scores_to_reviews(args.input, args.output, args.model)
