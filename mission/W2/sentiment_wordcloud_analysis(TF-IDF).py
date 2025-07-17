import pandas as pd
import re
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import json
from sklearn.feature_extraction.text import TfidfVectorizer

# NLTK 불용어 및 토크나이저 데이터 다운로드
nltk.download('stopwords')
nltk.download('punkt')
# nltk.download('punkt_tab')

print("필요한 라이브러리 및 NLTK 데이터 다운로드 완료.")

# 전처리 함수 정의
stop_words = set(stopwords.words('english'))
# 영화 리뷰 특화 불용어 추가
custom_stop_words = set([
    
    # 영화 리뷰 특화 불용어
    'film', 'movie', 'movies', 'jurassic', 'world', 'rebirth', 'park', 'scene', 'story', 'character', 
    'characters', 'franchise', 'dinosaur', 'dinosaurs', 'action', 'script', 'director', 'plot', 
    'sequel', 'series', 'entry', 'version', 'installment', 'entry', 'cinema', 'screen', 'audience',
    'effect', 'effects', 'cgi', 'visual', 'camera', 'performance', 'acting', 'cast', 'score', 
    'music', 'production', 'release', 'sound', 'dialogue', 'writer', 'writing', 'actor', 'actors', 'ounce', 'cenozoic',
    
    # 너무 일반적이거나 리뷰에 자주 등장하는 단어
    'good', 'bad', 'great', 'better', 'worst', 'best', 'fun', 'boring', 'okay', 'amazing', 'awful', 
    'cool', 'fine', 'okay', 'terrible', 'enjoyable', 'forgettable', 'predictable', 'interesting', 
    'uninteresting', 'fresh', 'new', 'old', 'classic', 'original', 'reboot', 'remake', 'nostalgia', 'nothing', 'proves', 'mediocre',
    
    # 영화명, 인물명, 브랜드명 등
    'spielberg', 'edwards', 'koepp', 'johnson', 'universal', 'hollywood', 'disney', 'dominion', 
    'ingen', 'hammond', 'scarlett', 'johansson', 'bailey',

    # 일반적인 불용어
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by',
    'can', "can't", 'cannot', 'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', "don't", 'down', 'during',
    'each', 'few', 'for', 'from', 'further',
    'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd", "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's",
    'i', "i'd", "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself',
    "let's", 'me', 'more', 'most', "mustn't", 'my', 'myself',
    'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own',
    'same', "shan't", 'she', "she'd", "she'll", "she's", 'should', "shouldn't", 'so', 'some', 'such',
    'than', 'that', "that's", 'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this', 'those', 'through', 'to', 'too',
    'under', 'until', 'up', 'very',
    'was', "wasn't", 'we', "we'd", "we'll", "we're", "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who', "who's", 'whom', 'why', "why's", 'with', "won't", 'would', "wouldn't",
    'you', "you'd", "you'll", "you're", "you've", 'your', 'yours', 'yourself', 'yourselves', 'theyre', 'youll', 'wasnt',

    # 특정 영화와 관련된 의미를 낼 수 없는 단어
    'jurassic', 'world', 'rebirth', 'park', 'movie', 'film', 'franchise', 'series', 'sequel', 'sequels', 'installment', 'installments', 'entry', 'entries',
    'dinosaur', 'dinosaurs', 'monster', 'monsters', 'creature', 'creatures', 'beast', 'beasts',
    'spielberg', 'edwards', 'gareth', 'johansson', 'scarlett', 'koepp', 'david', 'ali', 'bailey', 'friend', 'hammond', 'ingen',
    'action', 'adventure', 'horror', 'thriller', 'blockbuster',
    'character', 'characters', 'story', 'script', 'screenplay', 'plot', 'narrative', 'dialogue',
    'scene', 'scenes', 'visual', 'visuals', 'effects', 'vfx', 'cgi', 'special',
    'review', 'reviews', 'critic', 'critics', 'audience', 'audiences', 'fan', 'fans',
    'spanish', 'full', 'era',

    # 리뷰에 많이 등장하는 일반적인
    'one', 'two', 'three', 'seven', '30', '1993', '2025',
    'like', 'just', 'get', 'gets', 'getting', 'got',
    'make', 'makes', 'made', 'go', 'goes', 'going', 'gone',
    'come', 'comes', 'came',
    'see', 'sees', 'seen', 'seeing',
    'say', 'says',
    'know', 'knows',
    'think', 'thinks',
    'feel', 'feels', 'feeling',
    'look', 'looks', 'looking',
    'find', 'finds', 'found',
    'way', 'ways', 'time', 'times',
    'thing', 'things',
    'lot', 'lots', 'bit',
    'well', 'also', 'even', 'enough', 'much', 'still', 'really', 'ever', 'another', 'without', 'back', 'away',
    'new', 'old', 'big', 'long', 'best', 'better', 'good', 'bad', 'great', 'fun', 'solid', 'decent',
    'first', 'last', 'next', 'past', 'previous',
    'since', 'ago',
    's', 't', 're', 've', 'll', 'd', 'm',
    'us', 'mr', 'ms'
    # TF-IDF가 걸러내지 못하는, 정말로 의미 없는 단어 추가
])
all_stop_words = stop_words.union(custom_stop_words)


def preprocess_text(text):
    # 1. URL 제거
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # 2. @멘션 제거
    text = re.sub(r'@\w+', '', text)
    # 3. #해시태그 제거
    text = re.sub(r'#', '', text)
    # 4. 숫자 제거
    text = re.sub(r'\d+', '', text)
    # 5. 구두점 및 특수 문자 제거 (알파벳과 공백만 남김)
    text = re.sub(r'[^\w\s]', '', text)
    # 6. 소문자 변환
    text = text.lower()
    # 7. 토큰화
    tokens = word_tokenize(text)
    # 8. 불용어 제거 및 짧은 단어 제거 (2글자 이하)
    filtered_tokens = [word for word in tokens if word not in all_stop_words and len(word) > 2]
    return " ".join(filtered_tokens)

if __name__ == "__main__":
    json_file_path = "critic_reviews_labeled_jurassic.json"

    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            reviews_data = json.load(f)
        df = pd.DataFrame(reviews_data)
        print("데이터 로딩 완료.")
        print("\n데이터셋 상위 5행:")
        print(df.head())
        print("\n감성 분포:")
        print(df['sentiment'].value_counts())

        print("\n전처리 시작..")
        df['processed_text'] = df['text'].apply(preprocess_text)
        print("전처리 완료.")
        print("\n전처리된 데이터셋 상위 5행:")
        print(df.head())

        positive_reviews_text = df[df['sentiment'] == 'Positive']['processed_text'].tolist()
        negative_reviews_text = df[df['sentiment'] == 'Negative']['processed_text'].tolist()

        # TF-IDF 벡터라이저 초기화
        tfidf_vectorizer = TfidfVectorizer(max_features=1000) # 최대 1000개의 특징 단어 고려

        # 긍정 리뷰 TF-IDF 계산
        if positive_reviews_text:
            tfidf_matrix_positive = tfidf_vectorizer.fit_transform(positive_reviews_text)
            feature_names_positive = tfidf_vectorizer.get_feature_names_out()
            
            # 각 단어의 TF-IDF 점수를 평균 또는 합산하여 중요도 계산
            positive_tfidf_scores = {}
            for i, doc in enumerate(tfidf_matrix_positive):
                for col, score in zip(doc.indices, doc.data):
                    word = feature_names_positive[col]
                    positive_tfidf_scores[word] = max(positive_tfidf_scores.get(word, 0), score)
            
            # TF-IDF 점수가 높은 상위 200개 단어 샘플링
            top_positive_words_tfidf = dict(sorted(positive_tfidf_scores.items(), key=lambda item: item[1], reverse=True)[:200])
        else:
            top_positive_words_tfidf = {}

        # 부정 리뷰 TF-IDF 계산
        # 긍정/부정 단어의 상대적 중요도를 비교하기 위해 별도의 벡터라이저를 사용
        tfidf_vectorizer_neg = TfidfVectorizer(max_features=1000)
        if negative_reviews_text:
            tfidf_matrix_negative = tfidf_vectorizer_neg.fit_transform(negative_reviews_text)
            feature_names_negative = tfidf_vectorizer_neg.get_feature_names_out()

            negative_tfidf_scores = {}
            for i, doc in enumerate(tfidf_matrix_negative):
                for col, score in zip(doc.indices, doc.data):
                    word = feature_names_negative[col]
                    negative_tfidf_scores[word] = max(negative_tfidf_scores.get(word, 0), score)

            top_negative_words_tfidf = dict(sorted(negative_tfidf_scores.items(), key=lambda item: item[1], reverse=True)[:200])
        else:
            top_negative_words_tfidf = {}

        print("\nTF-IDF 기반 단어 중요도 계산 및 상위 200개 단어 샘플링 완료.")
        print(f"긍정 단어 수: {len(top_positive_words_tfidf)}")
        print(f"부정 단어 수: {len(top_negative_words_tfidf)}")

        # 긍정 워드 클라우드 생성
        positive_wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            min_font_size=10,
            max_words=200
        ).generate_from_frequencies(top_positive_words_tfidf)

        # 부정 워드 클라우드 생성
        negative_wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='black',
            min_font_size=10,
            max_words=200
        ).generate_from_frequencies(top_negative_words_tfidf)

        # 두 개의 워드 클라우드를 하나의 플롯에 그림
        plt.figure(figsize=(15, 7))

        plt.subplot(1, 2, 1)
        plt.imshow(positive_wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Positive Sentiment Word Cloud (TF-IDF)')

        plt.subplot(1, 2, 2)
        plt.imshow(negative_wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Negative Sentiment Word Cloud (TF-IDF)')

        plt.tight_layout()
        plt.show()

        print("\n워드 클라우드 시각화 완료.")

    except FileNotFoundError:
        print(f"오류: {json_file_path} 파일을 찾을 수 없습니다. scrape_reviews.py를 먼저 실행하여 데이터를 생성해주세요.")
    except Exception as e:
        print(f"데이터 처리 또는 워드 클라우드 생성 중 오류 발생: {e}")
