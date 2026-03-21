import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (
    confusion_matrix, accuracy_score, precision_score,
    recall_score, f1_score, roc_curve, roc_auc_score
)

# ===============================================
# Load dữ liệu
# ===============================================
file_path = "sentiment140_clean.csv"
# Tăng số lượng dữ liệu sử dụng từ 30% lên 50% để có nhiều dữ liệu hơn
data = pd.read_csv(file_path).sample(frac=0.5, random_state=42)
data = data.dropna(subset=['clean_text'])
data['clean_text'] = data['clean_text'].astype(str)

# Loại bỏ các văn bản quá ngắn
data = data[data['clean_text'].str.len() >= 3]

X = data['clean_text']
y = data['target']

# Chia dữ liệu train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ===============================================
# Sử dụng nhiều dữ liệu hơn để train (tăng từ 10% lên 30%)
# ===============================================
sample_frac = 0.3  # Tăng từ 0.1 lên 0.3
X_train_sample = X_train.sample(frac=sample_frac, random_state=42)
y_train_sample = y_train.loc[X_train_sample.index]

print(f"Số lượng mẫu training: {len(X_train_sample)}")

# TF-IDF vectorization với cải tiến
# Tăng max_features, thêm n-grams, và các tham số tối ưu
vectorizer = TfidfVectorizer(
    max_features=8000,           # Tăng từ 2000 lên 8000
    ngram_range=(1, 2),          # Thêm bigrams
    min_df=2,                    # Từ phải xuất hiện ít nhất 2 lần
    max_df=0.95,                 # Loại bỏ từ xuất hiện >95% documents
    sublinear_tf=True            # Sử dụng log scale cho term frequency
)
X_train_vec = vectorizer.fit_transform(X_train_sample)
X_test_vec = vectorizer.transform(X_test)

print(f"Số lượng features sau vectorization: {X_train_vec.shape[1]}")

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
# Huấn luyện & Dự đoán với KNN - Tối ưu k parameter
# ===============================================

# Tìm k tối ưu bằng GridSearchCV
print("\nĐang tìm k tối ưu...")
# Sử dụng subset nhỏ hơn để tìm k nhanh hơn
sample_size = min(20000, X_train_vec.shape[0])
indices = np.random.choice(X_train_vec.shape[0], sample_size, replace=False)
X_train_sample_small = X_train_vec[indices]
y_train_sample_small = y_train_sample.iloc[indices]

param_grid = {
    'n_neighbors': [3, 5, 7, 9, 11, 15]  # Thử nhiều giá trị k
}

knn_base = KNeighborsClassifier(n_jobs=-1, weights='distance')  # Sử dụng distance weights
grid_search = GridSearchCV(
    knn_base, param_grid, cv=3,
    scoring='accuracy', n_jobs=-1, verbose=1
)
grid_search.fit(X_train_sample_small, y_train_sample_small)

print(f"k tối ưu: {grid_search.best_params_['n_neighbors']}")
print(f"Best CV score: {grid_search.best_score_:.4f}")

# Huấn luyện với k tối ưu trên toàn bộ training sample
# Sử dụng distance weights để các điểm gần có ảnh hưởng lớn hơn
knn_model = KNeighborsClassifier(
    n_neighbors=grid_search.best_params_['n_neighbors'],
    weights='distance',  # Sử dụng distance weights thay vì uniform
    n_jobs=-1
)
knn_model.fit(X_train_vec, y_train_sample)

# Dự đoán nhãn phân loại (0 hoặc 1) với ngưỡng mặc định 0.5
y_pred_knn = knn_model.predict(X_test_vec)

# Dự đoán xác suất (Probability Predictions) - cần cho ROC curve
# predict_proba() trả về mảng [P(Negative), P(Positive)] cho mỗi mẫu
# Chỉ lấy xác suất của lớp Positive (cột thứ 2, index=1)
y_proba_knn = knn_model.predict_proba(X_test_vec)[:, 1]

# ===============================================
# Đánh giá mô hình
# ===============================================
# Đánh giá mô hình với True Labels (y_test) và Probability Predictions (y_proba_knn)
evaluate_model(y_test, y_pred_knn, y_proba_knn, "K-Nearest Neighbors (Improved TF-IDF)")
