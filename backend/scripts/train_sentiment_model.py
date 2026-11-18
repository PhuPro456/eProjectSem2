import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

# 1. DỮ LIỆU HUẤN LUYỆN (LABELED DATA)
# Bộ mẫu song ngữ Việt/Anh phủ đủ 5 khía cạnh x 3 nhãn (positive/neutral/negative).
# Trong thực tế có thể bổ sung bằng cách query từ PostgreSQL (bảng reviews) hoặc đọc CSV đã gán nhãn.
data = [
    # ===== Tiếng Anh — toàn tích cực =====
    {"text": "Brilliant book! Clear explanations and great code examples. Worth every penny.", "sentiment": "positive", "content": "positive", "understandability": "positive", "examples_code": "positive", "print_quality": "neutral", "price": "positive"},
    {"text": "A must-have for Python beginners. Very cheap and easy to follow.", "sentiment": "positive", "content": "positive", "understandability": "positive", "examples_code": "neutral", "print_quality": "neutral", "price": "positive"},
    {"text": "Loved every chapter. The content is rich, the examples run perfectly, and the print is crisp.", "sentiment": "positive", "content": "positive", "understandability": "neutral", "examples_code": "positive", "print_quality": "positive", "price": "neutral"},
    {"text": "Excellent theory, helpful exercises, sharp printing and a fair price.", "sentiment": "positive", "content": "positive", "understandability": "neutral", "examples_code": "positive", "print_quality": "positive", "price": "positive"},
    {"text": "This book is amazing. Easy to understand, practical code samples, good paper quality.", "sentiment": "positive", "content": "positive", "understandability": "positive", "examples_code": "positive", "print_quality": "positive", "price": "neutral"},
    {"text": "Clear explanations, working code, good paper, cheap. Highly recommend.", "sentiment": "positive", "content": "positive", "understandability": "positive", "examples_code": "positive", "print_quality": "positive", "price": "positive"},
    {"text": "Fantastic read, informative and practical, beautiful printing on thick paper.", "sentiment": "positive", "content": "positive", "understandability": "positive", "examples_code": "neutral", "print_quality": "positive", "price": "neutral"},
    # ===== Tiếng Anh — toàn tiêu cực =====
    {"text": "Boring and outdated. The print quality is terrible, very hard to read.", "sentiment": "negative", "content": "negative", "understandability": "negative", "examples_code": "neutral", "print_quality": "negative", "price": "neutral"},
    {"text": "Waste of money. Confusing explanations, buggy code, and blurry print.", "sentiment": "negative", "content": "negative", "understandability": "negative", "examples_code": "negative", "print_quality": "negative", "price": "negative"},
    {"text": "Terrible book. The content is shallow, the examples are full of bugs, and it's overpriced.", "sentiment": "negative", "content": "negative", "understandability": "neutral", "examples_code": "negative", "print_quality": "neutral", "price": "negative"},
    {"text": "Awful. Poor paper, smudged text, and the theory is outdated.", "sentiment": "negative", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "negative", "price": "neutral"},
    {"text": "Disappointing. Hard to follow, dull content, and far too expensive.", "sentiment": "negative", "content": "negative", "understandability": "negative", "examples_code": "neutral", "print_quality": "neutral", "price": "negative"},
    {"text": "Outdated examples, confusing text, blurry print, and overpriced. Avoid.", "sentiment": "negative", "content": "negative", "understandability": "negative", "examples_code": "negative", "print_quality": "negative", "price": "negative"},
    {"text": "Not worth the price. The content is shallow and the print is poor.", "sentiment": "negative", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "negative", "price": "negative"},
    # ===== Tiếng Anh — nội dung tốt / in ấn xấu =====
    {"text": "The content is brilliant and easy to understand, but the print quality is blurry and the price is too expensive.", "sentiment": "neutral", "content": "positive", "understandability": "positive", "examples_code": "neutral", "print_quality": "negative", "price": "negative"},
    {"text": "Great story and clear writing, but the paper is thin and the printing is faded.", "sentiment": "neutral", "content": "positive", "understandability": "positive", "examples_code": "neutral", "print_quality": "negative", "price": "neutral"},
    {"text": "I enjoyed the content, however the print is smudged and hard to read.", "sentiment": "neutral", "content": "positive", "understandability": "neutral", "examples_code": "neutral", "print_quality": "negative", "price": "neutral"},
    # ===== Tiếng Anh — nội dung tốt / giá xấu =====
    {"text": "Good paper quality but the content is too basic for this high price.", "sentiment": "negative", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "positive", "price": "negative"},
    {"text": "The theory is solid and well explained, but it's far too expensive for what you get.", "sentiment": "neutral", "content": "positive", "understandability": "positive", "examples_code": "neutral", "print_quality": "neutral", "price": "negative"},
    {"text": "Informative and practical, yet overpriced compared to similar books.", "sentiment": "neutral", "content": "positive", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "negative"},
    # ===== Tiếng Anh — nội dung tốt / code lỗi =====
    {"text": "The theory is good but the code snippets are full of bugs.", "sentiment": "neutral", "content": "positive", "understandability": "neutral", "examples_code": "negative", "print_quality": "neutral", "price": "neutral"},
    {"text": "Well written and easy to follow, but the examples don't compile.", "sentiment": "neutral", "content": "positive", "understandability": "positive", "examples_code": "negative", "print_quality": "neutral", "price": "neutral"},
    {"text": "Great concepts, clear explanations, however the code samples are buggy and outdated.", "sentiment": "neutral", "content": "positive", "understandability": "positive", "examples_code": "negative", "print_quality": "neutral", "price": "neutral"},
    {"text": "Fantastic content and crystal-clear explanations, though the code examples have a few bugs.", "sentiment": "neutral", "content": "positive", "understandability": "positive", "examples_code": "negative", "print_quality": "neutral", "price": "neutral"},
    # ===== Tiếng Anh — nội dung xấu / in ấn tốt =====
    {"text": "The printing is sharp and the binding is sturdy, but the content is shallow and repetitive.", "sentiment": "neutral", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "positive", "price": "neutral"},
    {"text": "Nice paper and clear print, yet the theory is outdated and boring.", "sentiment": "neutral", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "positive", "price": "neutral"},
    {"text": "The print is gorgeous but the writing is confusing and the price is steep.", "sentiment": "neutral", "content": "neutral", "understandability": "negative", "examples_code": "neutral", "print_quality": "positive", "price": "negative"},
    # ===== Tiếng Anh — hỗn hợp khác =====
    {"text": "Cheap and cheerful, easy to read, but the theory is outdated.", "sentiment": "neutral", "content": "negative", "understandability": "positive", "examples_code": "neutral", "print_quality": "neutral", "price": "positive"},
    {"text": "Well-structured content, helpful examples, fair price, but the paper is flimsy.", "sentiment": "neutral", "content": "positive", "understandability": "neutral", "examples_code": "positive", "print_quality": "negative", "price": "positive"},
    {"text": "Great value and clear writing, but the code samples are buggy.", "sentiment": "neutral", "content": "positive", "understandability": "positive", "examples_code": "negative", "print_quality": "neutral", "price": "positive"},
    {"text": "Beautiful print and cheap, yet the content is boring and hard to follow.", "sentiment": "neutral", "content": "negative", "understandability": "negative", "examples_code": "neutral", "print_quality": "positive", "price": "positive"},
    {"text": "The theory is outdated but the examples are excellent and the price is fair.", "sentiment": "neutral", "content": "negative", "understandability": "neutral", "examples_code": "positive", "print_quality": "neutral", "price": "positive"},
    {"text": "I love the plot and characters. The printing is sharp too. A bit pricey but worth it.", "sentiment": "positive", "content": "positive", "understandability": "neutral", "examples_code": "neutral", "print_quality": "positive", "price": "positive"},
    # ===== Tiếng Anh — chỉ giá =====
    {"text": "Way too expensive for a paperback.", "sentiment": "negative", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "negative"},
    {"text": "Such a cheap find, great value for money.", "sentiment": "positive", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "positive"},
    {"text": "The price is fair and reasonable.", "sentiment": "positive", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "positive"},
    {"text": "Overpriced and not worth the cost.", "sentiment": "negative", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "negative"},
    # ===== Tiếng Anh — chỉ in ấn =====
    {"text": "The print is blurry and the pages are smudged.", "sentiment": "negative", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "negative", "price": "neutral"},
    {"text": "Beautiful printing on thick, high-quality paper.", "sentiment": "positive", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "positive", "price": "neutral"},
    {"text": "Sharp text and sturdy binding, lovely paper.", "sentiment": "positive", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "positive", "price": "neutral"},
    # ===== Tiếng Anh — chỉ code / ví dụ =====
    {"text": "The code examples are buggy and won't run.", "sentiment": "negative", "content": "neutral", "understandability": "neutral", "examples_code": "negative", "print_quality": "neutral", "price": "neutral"},
    {"text": "Practical, working code samples throughout.", "sentiment": "positive", "content": "neutral", "understandability": "neutral", "examples_code": "positive", "print_quality": "neutral", "price": "neutral"},
    {"text": "Helpful exercises and clear code snippets.", "sentiment": "positive", "content": "neutral", "understandability": "neutral", "examples_code": "positive", "print_quality": "neutral", "price": "neutral"},
    # ===== Tiếng Anh — chỉ độ dễ hiểu =====
    {"text": "Very confusing and hard to follow.", "sentiment": "negative", "content": "neutral", "understandability": "negative", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Clear, straightforward explanations that make sense.", "sentiment": "positive", "content": "neutral", "understandability": "positive", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Easy to understand even for a complete beginner.", "sentiment": "positive", "content": "neutral", "understandability": "positive", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    # ===== Tiếng Anh — chỉ nội dung =====
    {"text": "The content is rich, deep and up to date.", "sentiment": "positive", "content": "positive", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Shallow, outdated content with nothing new.", "sentiment": "negative", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "A compelling plot and wonderful characters.", "sentiment": "positive", "content": "positive", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Boring story with a predictable, flat plot.", "sentiment": "negative", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    # ===== Tiếng Anh — trung tính / chung chung =====
    {"text": "The book has 300 pages and arrived on time.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "I bought this for my course. It is okay.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Received the book yesterday. Standard edition.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Average read, neither good nor bad.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "The content is fine but nothing remarkable. Average printing.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "It's an okay book. Does the job.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Standard textbook, nothing to complain about.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "The book arrived in good condition. 250 pages.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    # ===== Tiếng Việt — toàn tích cực =====
    {"text": "Sách rất hay, giải thích dễ hiểu, code mẫu chạy mượt. Đáng đồng tiền.", "sentiment": "positive", "content": "positive", "understandability": "positive", "examples_code": "positive", "print_quality": "neutral", "price": "positive"},
    {"text": "Cuốn này là tài liệu gối đầu giường cho ai học Python. Quá rẻ so với kiến thức.", "sentiment": "positive", "content": "positive", "understandability": "positive", "examples_code": "neutral", "print_quality": "neutral", "price": "positive"},
    {"text": "Nội dung sâu sắc, dễ hiểu, ví dụ thực tế, giấy in đẹp. Rất đáng mua.", "sentiment": "positive", "content": "positive", "understandability": "positive", "examples_code": "positive", "print_quality": "positive", "price": "positive"},
    {"text": "Sách hay, kiến thức mới, giải thích rõ ràng, giá rẻ.", "sentiment": "positive", "content": "positive", "understandability": "positive", "examples_code": "neutral", "print_quality": "neutral", "price": "positive"},
    {"text": "Tuyệt vời! Nội dung phong phú, code chạy tốt, giấy tốt, giá hợp lý.", "sentiment": "positive", "content": "positive", "understandability": "neutral", "examples_code": "positive", "print_quality": "positive", "price": "positive"},
    {"text": "Kiến thức sâu, giải thích dễ hiểu, đáng đồng tiền.", "sentiment": "positive", "content": "positive", "understandability": "positive", "examples_code": "neutral", "print_quality": "neutral", "price": "positive"},
    {"text": "Nội dung mới, hữu ích, in đẹp, đáng mua.", "sentiment": "positive", "content": "positive", "understandability": "neutral", "examples_code": "neutral", "print_quality": "positive", "price": "positive"},
    {"text": "Sách ổn, nội dung được, giá hợp lý.", "sentiment": "positive", "content": "positive", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "positive"},
    # ===== Tiếng Việt — toàn tiêu cực =====
    {"text": "Nội dung cũ rích, khó hiểu, sách in bị mờ chữ. Phí tiền.", "sentiment": "negative", "content": "negative", "understandability": "negative", "examples_code": "neutral", "print_quality": "negative", "price": "negative"},
    {"text": "Sách dở, nội dung nông, khó hiểu, code lỗi nhiều, đắt.", "sentiment": "negative", "content": "negative", "understandability": "negative", "examples_code": "negative", "print_quality": "neutral", "price": "negative"},
    {"text": "Quá thất vọng. Giấy xấu, chữ mờ, kiến thức lỗi thời.", "sentiment": "negative", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "negative", "price": "neutral"},
    {"text": "Phí tiền, nội dung chán, giải thích khó hiểu, giá quá đắt.", "sentiment": "negative", "content": "negative", "understandability": "negative", "examples_code": "neutral", "print_quality": "neutral", "price": "negative"},
    {"text": "Chữ mờ, giấy xấu, nội dung cũ, phí tiền.", "sentiment": "negative", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "negative", "price": "negative"},
    {"text": "Không hay, nội dung dở, khó hiểu.", "sentiment": "negative", "content": "negative", "understandability": "negative", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    # ===== Tiếng Việt — hỗn hợp =====
    {"text": "Sách viết khá ổn, nội dung sâu nhưng code ví dụ bị lỗi nhiều chỗ.", "sentiment": "neutral", "content": "positive", "understandability": "neutral", "examples_code": "negative", "print_quality": "neutral", "price": "neutral"},
    {"text": "Chất lượng giấy tốt, giao hàng nhanh. Nhưng kiến thức quá cơ bản, không như kỳ vọng.", "sentiment": "negative", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "positive", "price": "neutral"},
    {"text": "Nội dung hay và dễ hiểu, nhưng giấy in bị mờ và giá quá đắt.", "sentiment": "neutral", "content": "positive", "understandability": "positive", "examples_code": "neutral", "print_quality": "negative", "price": "negative"},
    {"text": "Kiến thức tốt, giải thích rõ, nhưng code mẫu bị lỗi.", "sentiment": "neutral", "content": "positive", "understandability": "positive", "examples_code": "negative", "print_quality": "neutral", "price": "neutral"},
    {"text": "Giấy đẹp, in rõ nhưng nội dung cũ và nhàm chán.", "sentiment": "neutral", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "positive", "price": "neutral"},
    {"text": "Sách hay nhưng quá đắt so với nội dung.", "sentiment": "neutral", "content": "positive", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "negative"},
    {"text": "Nội dung hay, dễ hiểu, nhưng giá hơi đắt.", "sentiment": "neutral", "content": "positive", "understandability": "positive", "examples_code": "neutral", "print_quality": "neutral", "price": "negative"},
    {"text": "Sách in đẹp, giấy tốt nhưng nội dung khó hiểu.", "sentiment": "neutral", "content": "neutral", "understandability": "negative", "examples_code": "neutral", "print_quality": "positive", "price": "neutral"},
    {"text": "Nội dung hay nhưng code lỗi và giấy mờ.", "sentiment": "neutral", "content": "positive", "understandability": "neutral", "examples_code": "negative", "print_quality": "negative", "price": "neutral"},
    {"text": "Dễ hiểu, giá rẻ, nhưng nội dung hơi cũ.", "sentiment": "neutral", "content": "negative", "understandability": "positive", "examples_code": "neutral", "print_quality": "neutral", "price": "positive"},
    {"text": "Giá rẻ nhưng giấy in mờ.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "negative", "price": "positive"},
    # ===== Tiếng Việt — chỉ một khía cạnh =====
    {"text": "Giá quá đắt, không đáng.", "sentiment": "negative", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "negative"},
    {"text": "Rẻ bất ngờ, rất đáng tiền.", "sentiment": "positive", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "positive"},
    {"text": "Chữ in bị mờ, giấy mỏng.", "sentiment": "negative", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "negative", "price": "neutral"},
    {"text": "Giấy tốt, in sắc nét.", "sentiment": "positive", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "positive", "price": "neutral"},
    {"text": "Code ví dụ bị lỗi, không chạy được.", "sentiment": "negative", "content": "neutral", "understandability": "neutral", "examples_code": "negative", "print_quality": "neutral", "price": "neutral"},
    {"text": "Ví dụ thực tế, code chạy mượt.", "sentiment": "positive", "content": "neutral", "understandability": "neutral", "examples_code": "positive", "print_quality": "neutral", "price": "neutral"},
    {"text": "Giải thích khó hiểu, rối rắm.", "sentiment": "negative", "content": "neutral", "understandability": "negative", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Dễ hiểu, giải thích rõ ràng.", "sentiment": "positive", "content": "neutral", "understandability": "positive", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Nội dung sâu sắc, kiến thức mới.", "sentiment": "positive", "content": "positive", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Nội dung cũ, nông, chán.", "sentiment": "negative", "content": "negative", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Code mẫu chạy tốt, ví dụ hay, giấy in đẹp, giá rẻ.", "sentiment": "positive", "content": "neutral", "understandability": "neutral", "examples_code": "positive", "print_quality": "positive", "price": "positive"},
    {"text": "Ví dụ phong phú, code rõ ràng, dễ làm theo.", "sentiment": "positive", "content": "neutral", "understandability": "positive", "examples_code": "positive", "print_quality": "neutral", "price": "neutral"},
    # ===== Tiếng Việt — trung tính / chung chung =====
    {"text": "Sách có 300 trang, giao hàng đúng hẹn.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Mua cho khóa học, đọc tạm được.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Sách bình thường, không có gì đặc biệt.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Sách đọc được, không có gì nổi bật.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
    {"text": "Bình thường, đúng như mô tả.", "sentiment": "neutral", "content": "neutral", "understandability": "neutral", "examples_code": "neutral", "print_quality": "neutral", "price": "neutral"},
]

def train_model():
    print("1. Đang chuẩn bị dữ liệu...")
    df = pd.DataFrame(data)
    
    X = df['text']
    # Chúng ta dự đoán 6 nhãn cùng lúc: 1 sentiment chung + 5 khía cạnh
    y_columns = ['sentiment', 'content', 'understandability', 'examples_code', 'print_quality', 'price']
    y = df[y_columns]

    # Cắt tập train/test (Vì dữ liệu ít nên để test_size nhỏ)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("2. Đang xây dựng Pipeline (TF-IDF + Logistic Regression)...")
    # Sử dụng Pipeline để gom Tfidf và Model thành 1 file duy nhất cho gọn
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
        # MultiOutputClassifier giúp LogisticRegression có thể dự đoán nhiều cột (aspects) cùng lúc
        ('clf', MultiOutputClassifier(LogisticRegression(C=10.0, max_iter=2000, class_weight='balanced')))
    ])

    print("3. Đang huấn luyện mô hình...")
    pipeline.fit(X_train, y_train)

    print("4. Đánh giá mô hình (Classification Report):")
    y_pred = pipeline.predict(X_test)
    
    # In báo cáo cho từng cột
    for i, col in enumerate(y_columns):
        print(f"\n--- Báo cáo cho: {col.upper()} ---")
        print(classification_report(y_test.iloc[:, i], y_pred[:, i], zero_division=0))

    print("5. Huấn luyện lại trên TOÀN BỘ dữ liệu cho mô hình triển khai...")
    # Báo cáo ở bước 4 chỉ để tham khảo; mô hình lưu lại được fit trên tất cả mẫu
    # để tận dụng tối đa dữ liệu gán nhãn (chuẩn thực hành khi deploy).
    pipeline.fit(X, y)

    print("6. Lưu mô hình...")
    # Tạo thư mục ml_models nếu chưa có
    os.makedirs("app/ml_models", exist_ok=True)
    model_path = "app/ml_models/sentiment_pipeline.joblib"
    joblib.dump(pipeline, model_path)
    
    print(f"Hoàn tất! Mô hình đã được lưu tại: {model_path}")

if __name__ == "__main__":
    train_model()