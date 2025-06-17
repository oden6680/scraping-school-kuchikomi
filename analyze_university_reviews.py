import json
import os
import sys
import argparse
import urllib.request
from tqdm import tqdm
from janome.tokenizer import Tokenizer
from gensim.models import KeyedVectors
import numpy as np

def analyze_university_reviews(input_file, output_file, model_path):
    """
    大学の口コミデータを分析し、ネガティブスコアと単語頻度を計算する
    
    Args:
        input_file (str): 入力JSONファイルのパス（aggregated_reviews_by_university.json）
        output_file (str): 出力JSONファイルのパス
        model_path (str): fastTextモデルのパス
    """
    print("大学口コミの感情分析と単語頻度分析を開始します...")
    
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
        # fastTextモデルの読み込み方法を修正
        from gensim.models.fasttext import load_facebook_model
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
    
    output = []
    for uni in data:
        university_name = uni['university_name']
        print(f"{university_name}の分析を開始します...")
        
        all_words = []
        neg_scores = []
        
        for rev in uni['reviews']:
            if not rev or rev.isspace():  # 空の口コミをスキップ
                continue
                
            # 1) 形態素解析して単語リスト
            tokens = [t.surface for t in tokenizer.tokenize(rev) if t.part_of_speech.startswith('名詞,一般')]
            all_words.extend(tokens)
            
            # 2) レビュー全体のベクトルを平均ベクトルで近似
            vecs = []
            for w in tokens:
                if w in model:
                    vecs.append(model[w])
            
            if vecs:
                review_vec = np.mean(vecs, axis=0)
                # ネガティブ度合い = cos(review_vec, axis)
                neg = np.dot(review_vec, axis) / (np.linalg.norm(review_vec) * np.linalg.norm(axis))
            else:
                neg = 0.0
            
            neg_scores.append(neg)
        
        # 大学全体のネガティブ度合い = レビューごとの平均
        uni_neg = float(np.mean(neg_scores)) if neg_scores else 0.0
        
        # 単語出現頻度とネガティブ/ポジティブスコアを計算
        word_info = {}
        for w in all_words:
            # 単語の出現回数をカウント
            if w not in word_info:
                word_info[w] = {"count": 0, "sentiment_score": 0.0}
            word_info[w]["count"] += 1
            
            # 単語のネガティブ/ポジティブスコアを計算（単語ベクトルと感情軸のコサイン類似度）
            if w in model:
                word_vec = model[w]
                # ベクトルのノルムが0でないことを確認
                word_norm = np.linalg.norm(word_vec)
                axis_norm = np.linalg.norm(axis)
                if word_norm > 0 and axis_norm > 0:
                    sentiment = np.dot(word_vec, axis) / (word_norm * axis_norm)
                    # 既存のスコアと平均を取る（同じ単語が複数回出現する場合）
                    current_count = word_info[w]["count"]
                    current_score = word_info[w]["sentiment_score"]
                    word_info[w]["sentiment_score"] = ((current_count - 1) * current_score + sentiment) / current_count
        
        # 頻度順にソート
        sorted_word_info = {
            k: {
                "count": v["count"], 
                "sentiment_score": float(v["sentiment_score"]),
                "sentiment": "positive" if v["sentiment_score"] < -0.01 else ("negative" if v["sentiment_score"] > 0.01 else "neutral")
            } 
            for k, v in sorted(word_info.items(), key=lambda item: item[1]["count"], reverse=True)
        }
        
        output.append({
            "university_name": university_name,
            "negative_score": uni_neg,
            "word_info": sorted_word_info,
            "review_count": len(uni['reviews']),
            "analyzed_review_count": len(neg_scores)
        })
        
        print(f"{university_name}の分析が完了しました。ネガティブスコア: {uni_neg:.4f}, 分析した口コミ数: {len(neg_scores)}")
    
    # 結果をJSONにダンプして保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"分析が完了しました。結果は {output_file} に保存されました。")
    return output

def download_fasttext_model(model_url, model_path):
    """
    fastTextモデルをダウンロードする
    
    Args:
        model_url (str): モデルのURL
        model_path (str): 保存先のパス
    
    Returns:
        bool: ダウンロードが成功したかどうか
    """
    if os.path.exists(model_path):
        print(f"モデルファイルが既に存在します: {model_path}")
        return True
    
    print(f"fastTextモデルをダウンロードしています: {model_url}")
    print(f"保存先: {model_path}")
    print("※ダウンロードには時間がかかる場合があります（約1.5GB）")
    
    try:
        # プログレスバー付きでダウンロード
        class DownloadProgressBar(tqdm):
            def update_to(self, b=1, bsize=1, tsize=None):
                if tsize is not None:
                    self.total = tsize
                self.update(b * bsize - self.n)
        
        with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc="Downloading") as t:
            urllib.request.urlretrieve(model_url, model_path, reporthook=t.update_to)
        
        print(f"ダウンロードが完了しました: {model_path}")
        return True
    except Exception as e:
        print(f"ダウンロードエラー: {e}")
        return False

if __name__ == "__main__":
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='大学口コミの感情分析と単語頻度分析')
    parser.add_argument('--input', '-i', default='aggregated_reviews_by_university.json',
                        help='入力JSONファイルのパス（デフォルト: aggregated_reviews_by_university.json）')
    parser.add_argument('--output', '-o', default='university_sentiment_analysis.json',
                        help='出力JSONファイルのパス（デフォルト: university_sentiment_analysis.json）')
    parser.add_argument('--model', '-m', default='cc.ja.300.bin',
                        help='fastTextモデルのパス（デフォルト: cc.ja.300.bin）')
    parser.add_argument('--download', '-d', action='store_true',
                        help='fastTextモデルをダウンロードする')
    
    args = parser.parse_args()
    
    # fastTextモデルのダウンロード（必要な場合）
    if args.download:
        model_url = "https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.ja.300.bin.gz"
        print("※注意: モデルファイルは圧縮形式でダウンロードされます。")
        print("ダウンロード後、手動で解凍してください: gunzip cc.ja.300.bin.gz")
        print("または、以下のコマンドを実行してください:")
        print("!gunzip cc.ja.300.bin.gz")
        sys.exit(0)
    
    # 入力ファイルの存在確認
    if not os.path.exists(args.input):
        print(f"エラー: 入力ファイルが見つかりません: {args.input}")
        sys.exit(1)
    
    # モデルファイルの存在確認
    if not os.path.exists(args.model):
        print(f"エラー: モデルファイルが見つかりません: {args.model}")
        print("fastTextモデルをダウンロードするには、--download オプションを使用してください。")
        print("例: python analyze_university_reviews.py --download")
        sys.exit(1)
    
    # 分析の実行
    analyze_university_reviews(args.input, args.output, args.model)
