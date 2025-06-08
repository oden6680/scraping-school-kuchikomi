import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import os
import random
import argparse
from datetime import datetime

def load_urls(file_path):
    """URLリストをJSONファイルから読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        urls = json.load(f)
    return urls

def extract_university_name(title):
    """タイトルから大学名を抽出する"""
    if 'の情報満載' in title:
        return title.split('の情報満載')[0]
    return title.split('｜')[0] if '｜' in title else title

RATING_NAME_MAP = {
    '口コミ内容': 'review_content',
    '投稿日': 'post_date',
    '口コミID': 'review_id',
    '総合評価': 'overall_rating',
    '総合評価_詳細': 'overall_rating_detail',
    '研究室・ゼミ': 'laboratory_seminar',
    '研究室・ゼミ_詳細': 'laboratory_seminar_detail',
    '就職・進学': 'career',
    '就職・進学_詳細': 'career_detail',
    'アクセス・立地': 'access_location',
    'アクセス・立地_詳細': 'access_location_detail',
    '施設・設備': 'facilities',
    '施設・設備_詳細': 'facilities_detail',
    '友人・恋愛': 'friendship_romance',
    '友人・恋愛_詳細': 'friendship_romance_detail',
    '学生生活': 'student_life',
    '学生生活_詳細': 'student_life_detail',
    '学科で学ぶ内容': 'department_curriculum',
    '学科で学ぶ内容_詳細': 'department_curriculum_detail',
    '学科の男女比': 'gender_ratio',
    '学科の男女比_詳細': 'gender_ratio_detail',
    '就職先・進学先': 'career_path',
    '就職先・進学先_詳細': 'career_path_detail',
    '志望動機': 'motivation',
    '志望動機_詳細': 'motivation_detail'
}

def extract_json_reviews(html_content):
    """HTMLからJSON形式の口コミデータを抽出する"""
    import re
    
    reviews = []
    
    pattern = r'"@type":\s*"Answer",\s*"text":\s*"([^"]*)",\s*"dateCreated":\s*"([^"]*)"[^}]*'
    matches = re.findall(pattern, html_content)
    
    for text, date in matches:
        review_data = {
            'review_content': text,
            'post_date': date.split('T')[0] if 'T' in date else date
        }
        reviews.append(review_data)
    
    return reviews

def extract_review_ratings(html_content):
    """HTMLから評価項目を抽出する"""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    review_list = soup.select_one('.mod-reviewList')
    if not review_list:
        print("警告: 口コミリストが見つかりませんでした")
        return []
    
    review_items = review_list.select('li[id^="answer_"]')
    if not review_items:
        print("警告: 口コミアイテムが見つかりませんでした")
        review_items = review_list.select('li')
    
    all_reviews = []
    
    for item in review_items:
        review_data = {}
        review_id = item.get('id', '')
        if review_id:
            review_data['review_id'] = review_id
        
        rating_lists = item.select('.js-mod-reviewList-list')
        if not rating_lists:
            rating_items = item.select('.schMod-reviewList-titleTop')
            process_rating_items(rating_items, review_data)
        else:
            for rating_list in rating_lists:
                rating_items = rating_list.select('.schMod-reviewList-titleTop')
                process_rating_items(rating_items, review_data)
        
        if review_data:
            all_reviews.append(review_data)
    
    return all_reviews

def process_rating_items(rating_items, review_data):
    """評価項目を処理して辞書に追加する"""
    for item in rating_items:
        title_elem = item.select_one('.schMod-reviewList-title')
        rating_elem = item.select_one('.schMod-reviewList-ic')
        
        if title_elem and rating_elem:
            title = title_elem.text.strip()
            rating = rating_elem.text.strip()
            
            if title in RATING_NAME_MAP:
                eng_title = RATING_NAME_MAP[title]
                review_data[eng_title] = rating
            else:
                review_data[title] = rating
        
        txt_elem = item.find_next_sibling('div', class_='mod-reviewList-txt')
        if txt_elem and title_elem:
            title = title_elem.text.strip()
            txt = txt_elem.text.strip()
            
            if f'{title}_詳細' in RATING_NAME_MAP:
                eng_title = RATING_NAME_MAP[f'{title}_詳細']
                review_data[eng_title] = txt
            else:
                review_data[f'{title}_detail'] = txt
            
            if title == '総合評価':
                review_data['review_content'] = txt

def scrape_reviews(url, max_reviews=20):
    """指定されたURLから口コミ情報をスクレイピングする"""
    print(f"スクレイピング中: {url}")
    print(f"最大取得件数: {max_reviews}件")
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        'Referer': 'https://www.minkou.jp/university/'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.text if soup.title else ""
        university_name = extract_university_name(title)
        
        school_id = url.rstrip('/').split('/')[-1]
        base_review_url = f"https://www.minkou.jp/university/school/review/{school_id}/"
        
        all_reviews = []
        
        page = 1
        
        max_pages = (max_reviews + 9) // 10
        
        while len(all_reviews) < max_reviews and page <= max_pages:
            if page == 1:
                review_url = base_review_url
            else:
                review_url = f"{base_review_url}page={page}#reviewlist"
            
            print(f"口コミページ {page} にアクセス中: {review_url}")
            
            review_response = requests.get(review_url, headers=headers)
            review_response.raise_for_status()
            
            html_content = review_response.text
            
            reviews_json = extract_json_reviews(html_content)
            reviews_html = extract_review_ratings(html_content)
            page_reviews = []
            
            if reviews_html:
                page_reviews = reviews_html
                print(f"HTMLから{len(page_reviews)}件の口コミと評価項目を取得しました")
            elif reviews_json:
                page_reviews = reviews_json
                print(f"JSONから{len(page_reviews)}件の口コミを取得しました")
            else:
                print("標準的な方法で口コミデータが見つかりませんでした。別の方法で抽出を試みます。")
                review_soup = BeautifulSoup(html_content, 'html.parser')
                
                review_elements = review_soup.select('.reviewBox, .mod-reviewBox, .mod-review, .review')
                
                if not review_elements:
                    print(f"警告: 口コミ要素が見つかりませんでした。別のセレクタを試します。")
                    review_elements = review_soup.select('[class*="review"]')
                
                for review_elem in review_elements:
                    review_data = {}
                    poster_info = review_elem.select_one('.reviewerInforamtion, .reviewerInformation, .mod-reviewerInfo')
                    if poster_info:
                        date_elem = poster_info.select_one('.date')
                        review_data['post_date'] = date_elem.text.strip() if date_elem else "不明"
                        
                        poster_attrs = poster_info.select('.reviewerAttribute, .mod-reviewerAttribute')
                        for attr in poster_attrs:
                            attr_text = attr.text.strip()
                            if '：' in attr_text:
                                key, value = attr_text.split('：', 1)
                                key_eng = RATING_NAME_MAP.get(key.strip(), key.strip())
                                review_data[key_eng] = value.strip()
                    
                    review_text = review_elem.select_one('.reviewText, .mod-reviewText')
                    if review_text:
                        review_data['review_content'] = review_text.text.strip()
                    
                    ratings = review_elem.select('.ratingItem, .mod-ratingItem')
                    for rating in ratings:
                        rating_name = rating.select_one('.ratingName, .mod-ratingName')
                        rating_value = rating.select_one('.ratingValue, .mod-ratingValue')
                        if rating_name and rating_value:
                            key = rating_name.text.strip()
                            key_eng = RATING_NAME_MAP.get(key, key)
                            review_data[key_eng] = rating_value.text.strip()
                    
                    if review_data:
                        page_reviews.append(review_data)
            
            if not page_reviews:
                print(f"警告: 口コミが見つかりませんでした: {review_url}")
                print(f"ページ構造の一部: {html_content[:500]}...")
                break
            
            all_reviews.extend(page_reviews)
            print(f"現在の取得件数: {len(all_reviews)}件")
            
            next_page_link = BeautifulSoup(html_content, 'html.parser').select_one('li.next a')
            if not next_page_link:
                print("次のページが見つかりません。スクレイピングを終了します。")
                break
            
            if len(all_reviews) >= max_reviews:
                print(f"最大取得件数({max_reviews}件)に達しました。")
                all_reviews = all_reviews[:max_reviews]
                break
            
            page += 1
            
            delay = 1 + random.uniform(0, 1)
            print(f"{delay:.2f}秒待機中...")
            time.sleep(delay)
        
        print(f"合計{len(all_reviews)}件の口コミを取得しました")
        
        return {
            'university_name': university_name,
            'url': url,
            'review_url': base_review_url,
            'reviews': all_reviews
        }
        
    except Exception as e:
        print(f"エラーが発生しました: {url} - {str(e)}")
        return {
            'university_name': url.split('/')[-2] if url.endswith('/') else url.split('/')[-1],
            'url': url,
            'reviews': [],
            'error': str(e)
        }

def save_to_json(data, output_dir):
    """スクレイピングしたデータをJSONファイルに保存"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for university_data in data:
        filename = f"{output_dir}/{university_data['university_name']}_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(university_data, f, ensure_ascii=False, indent=2)
        print(f"保存完了: {filename}")

def save_to_csv(data, output_dir):
    """スクレイピングしたデータをCSVファイルに保存"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{output_dir}/university_reviews_{timestamp}.csv"
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        f.write('University,URL,Date,Review\n')
        
        for university_data in data:
            university_name = university_data['university_name']
            url = university_data['url']
            
            for review in university_data['reviews']:
                date = review.get('post_date', '')
                content = review.get('review_content', '')
                
                uni_name_esc = university_name.replace('"', '""')
                url_esc = url.replace('"', '""')
                date_esc = date.replace('"', '""')
                content_esc = content.replace('"', '""')
                
                uni_name_csv = f'"{uni_name_esc}"'
                url_csv = f'"{url_esc}"'
                date_csv = f'"{date_esc}"'
                content_csv = f'"{content_esc}"'
                
                f.write(f'{uni_name_csv},{url_csv},{date_csv},{content_csv}\n')
    
    print(f"CSVファイルに保存完了: {filename}")

def main():
    parser = argparse.ArgumentParser(description='大学の口コミ情報をスクレイピングするツール')
    parser.add_argument('--test', action='store_true', help='テストモードで実行（少数のURLのみ）')
    parser.add_argument('--delay', type=float, default=3.0, help='リクエスト間の遅延時間（秒）')
    parser.add_argument('--output', type=str, default='reviews_data', help='出力ディレクトリ')
    parser.add_argument('--csv', action='store_true', help='CSVファイルも出力する（デフォルトはJSONのみ）')
    parser.add_argument('--max-reviews', type=int, default=20, help='1大学あたりの最大取得口コミ数（デフォルト: 20件）')
    args = parser.parse_args()
    
    url_file = 'test_urls.json' if args.test else 'urlList.json'
    output_dir = args.output
    delay_seconds = args.delay
    output_csv = args.csv
    max_reviews = args.max_reviews
    
    print(f"実行モード: {'テスト' if args.test else '通常'}")
    print(f"使用ファイル: {url_file}")
    print(f"遅延時間: {delay_seconds}秒")
    print(f"出力ディレクトリ: {output_dir}")
    print(f"出力形式: {'JSON+CSV' if output_csv else 'JSONのみ'}")
    print(f"最大取得口コミ数: {max_reviews}件/大学")
    
    urls = load_urls(url_file)
    print(f"{len(urls)}件のURLを読み込みました")
    
    all_data = []
    for i, url in enumerate(urls):
        print(f"進捗: {i+1}/{len(urls)}")
        university_data = scrape_reviews(url, max_reviews=max_reviews)
        all_data.append(university_data)
        
        if i < len(urls) - 1:
            delay = delay_seconds + random.uniform(0, 2)
            print(f"{delay:.2f}秒待機中...")
            time.sleep(delay)
    
    save_to_json(all_data, output_dir)

    if output_csv:
        save_to_csv(all_data, output_dir)
    
    print("スクレイピング完了！")

if __name__ == "__main__":
    main()
