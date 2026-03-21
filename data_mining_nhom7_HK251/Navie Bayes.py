# ===============================================
# 3.3.5.a Sử dụng Multinomial Naive Bayes (sparse)
# ===============================================

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    confusion_matrix, accuracy_score, precision_score,
    recall_score, f1_score, roc_curve, roc_auc_score
)


# ===============================================
# Chuẩn bị dữ liệu
# ===============================================

# Dữ liệu đã được làm sạch
df = pd.read_csv("sentiment140_clean.csv")
df = df.dropna(subset=['clean_text'])
df['clean_text'] = df['clean_text'].astype(str)

# Loại bỏ các văn bản quá ngắn (ít thông tin)
df = df[df['clean_text'].str.len() >= 3]

# Biến văn bản → TF-IDF với cải tiến
# Sử dụng n-grams (1,2) để bắt được cụm từ quan trọng
# Tăng max_features để giữ nhiều từ quan trọng hơn
# min_df và max_df để loại bỏ từ quá hiếm/quá phổ biến
vectorizer = TfidfVectorizer(
    max_features=15000,          # Tăng từ 5000 lên 15000
    ngram_range=(1, 2),          # Thêm bigrams
    min_df=2,                    # Từ phải xuất hiện ít nhất 2 lần
    max_df=0.95,                 # Loại bỏ từ xuất hiện >95% documents
    sublinear_tf=True            # Sử dụng log scale cho term frequency
)
X_tfidf = vectorizer.fit_transform(df["clean_text"])
y = df["target"].values

print(f"Số lượng features sau vectorization: {X_tfidf.shape[1]}")

# Chia dữ liệu train / test
X_train, X_test, y_train, y_test = train_test_split(
    X_tfidf, y, test_size=0.3, random_state=42, stratify=y
)


# ===============================================
# Hàm đánh giá mô hình
# ===============================================

def plot_confusion_matrix(y_true, y_pred, model_name):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 4))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
                xticklabels=['Negative (0)', 'Positive (1)'],
                yticklabels=['Negative (0)', 'Positive (1)'])
    plt.title(f'Confusion Matrix for {model_name}')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.tight_layout()
    plt.show()


def plot_roc_curve(y_true, y_proba, model_name):
    """
    Vẽ đường cong ROC dựa trên True Labels (y_true) và Probability Predictions (y_proba)
    
    Args:
        y_true: Giá trị lớp thực tế (True Labels)
        y_proba: Dự đoán xác suất (Probability Predictions) - chỉ lấy xác suất của lớp Positive
        model_name: Tên mô hình
    """
    # Tính toán FPR, TPR cho tất cả các ngưỡng cắt
    fpr, tpr, thresholds = roc_curve(y_true, y_proba)
    
    # Tính AUC score
    auc_score = roc_auc_score(y_true, y_proba)
    
    # Vẽ ROC curve
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, 
             label=f'ROC curve (AUC = {auc_score:.4f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', 
             label='Random Classifier (AUC = 0.5000)')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate (FPR)', fontsize=12)
    plt.ylabel('True Positive Rate (TPR / Recall)', fontsize=12)
    plt.title(f'ROC Curve for {model_name}', fontsize=14, fontweight='bold')
    plt.legend(loc="lower right", fontsize=11)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    print(f"  AUC Score  : {auc_score:.4f}")
    return auc_score


def evaluate_model(y_true, y_pred, y_proba, model_name):
    """
    Đánh giá mô hình với các metrics và vẽ confusion matrix + ROC curve
    
    Args:
        y_true: Giá trị lớp thực tế (True Labels)
        y_pred: Dự đoán nhãn phân loại (0 hoặc 1)
        y_proba: Dự đoán xác suất (Probability Predictions) - chỉ lấy xác suất của lớp Positive
        model_name: Tên mô hình
    """
    print(f"\n{'='*60}")
    print(f"Đánh giá cho {model_name}:")
    print(f"{'='*60}")
    print(f"  Accuracy  : {accuracy_score(y_true, y_pred):.4f}")
    print(f"  Precision : {precision_score(y_true, y_pred):.4f}")
    print(f"  Recall    : {recall_score(y_true, y_pred):.4f}")
    print(f"  F1 Score  : {f1_score(y_true, y_pred):.4f}")
    
    # Vẽ Confusion Matrix
    plot_confusion_matrix(y_true, y_pred, model_name)
    
    # Vẽ ROC Curve
    print(f"\nROC Curve Analysis:")
    auc_score = plot_roc_curve(y_true, y_proba, model_name)


# ===============================================
# Huấn luyện và dự đoán với tối ưu hyperparameters
# ===============================================

# Tìm alpha tối ưu bằng GridSearchCV
print("\nĐang tìm hyperparameters tối ưu...")
param_grid = {
    'alpha': [0.1, 0.5, 1.0, 1.5, 2.0]
}

# Sử dụng subset nhỏ hơn để tìm alpha nhanh hơn
sample_size = min(50000, X_train.shape[0])
indices = np.random.choice(X_train.shape[0], sample_size, replace=False)
X_train_sample = X_train[indices]
y_train_sample = y_train[indices]

nb_base = MultinomialNB()
grid_search = GridSearchCV(
    nb_base, param_grid, cv=3, 
    scoring='accuracy', n_jobs=-1, verbose=1
)
grid_search.fit(X_train_sample, y_train_sample)

print(f"Alpha tối ưu: {grid_search.best_params_['alpha']}")
print(f"Best CV score: {grid_search.best_score_:.4f}")

# Huấn luyện với alpha tối ưu trên toàn bộ training set
nb_model = MultinomialNB(alpha=grid_search.best_params_['alpha'])
nb_model.fit(X_train, y_train)

# Dự đoán nhãn phân loại (0 hoặc 1) với ngưỡng mặc định 0.5
y_pred_nb = nb_model.predict(X_test)

# Dự đoán xác suất (Probability Predictions) - cần cho ROC curve
# predict_proba() trả về mảng [P(Negative), P(Positive)] cho mỗi mẫu
# Chỉ lấy xác suất của lớp Positive (cột thứ 2, index=1)
y_proba_nb = nb_model.predict_proba(X_test)[:, 1]

# Đánh giá mô hình với True Labels (y_test) và Probability Predictions (y_proba_nb)
evaluate_model(y_test, y_pred_nb, y_proba_nb, "Multinomial Naive Bayes (Improved TF-IDF)")
