# Sentiment Analysis on Twitter - Data Mining Project

Dự án phân tích cảm xúc người dùng trên nền tảng Twitter sử dụng các kỹ thuật Khai phá dữ liệu và Học máy. Đây là Bài tập lớn môn **Khai phá dữ liệu (CO3069)** - Học kỳ 251 - Đại học Bách Khoa TP.HCM.


## 📖 Giới thiệu đề tài

Đề tài tập trung xây dựng hệ thống tự động phân loại cảm xúc (Tích cực/Tiêu cực) của các tweet nhằm hỗ trợ doanh nghiệp thấu hiểu khách hàng và giám sát dư luận xã hội.

* **Tập dữ liệu:** Sentiment140 gồm 1.600.000 tweet đã gán nhãn.


* **Công cụ:** Python (NLTK, Scikit-learn, Pandas, Matplotlib, Seaborn).



## 🛠 Quy trình thực hiện

### 1. Tiền xử lý dữ liệu (Data Preprocessing)

Do đặc thù tweet chứa nhiều nhiễu, nhóm đã thực hiện chuỗi các bước:

* **Làm sạch văn bản:** Loại bỏ URL, mentions (@user), hashtag (#), số và ký tự đặc biệt.


* **Chuẩn hóa:** Chuyển về chữ thường, xử lý khoảng trắng thừa.


* **Loại bỏ từ dừng (Stopwords Removal):** Loại bỏ các từ phổ biến không mang giá trị cảm xúc (the, is, at...).


* **Đưa từ về gốc (Stemming):** Sử dụng thuật toán PorterStemmer.



### 2. Biểu diễn đặc trưng

Sử dụng phương pháp **TF-IDF (Term Frequency-Inverse Document Frequency)** để chuyển đổi văn bản thành vector số học, giúp mô hình hiểu được tầm quan trọng của các từ ngữ.

### 3. Các mô hình huấn luyện

Nhóm đã hiện thực và thử nghiệm 3 thuật toán:

1. **K-Nearest Neighbors (KNN):** Dựa trên khoảng cách giữa các điểm dữ liệu.


2. **Multinomial Naive Bayes (MNB):** Dựa trên xác suất có điều kiện, phù hợp với dữ liệu văn bản rời rạc.


3. **Logistic Regression (LR):** Mô hình phân loại tuyến tính dự đoán xác suất qua hàm Sigmoid.



## 📊 Kết quả thực nghiệm

So sánh hiệu suất giữa 3 mô hình trên tập kiểm thử:

| Chỉ số | KNN | MNB | **Logistic Regression** |
| --- | --- | --- | --- |
| **Accuracy** | 0.6377 | 0.7692 | **0.7880** |
| **Precision** | 0.6174 | 0.7693 | **0.7768** |
| **Recall** | 0.7220 | 0.7688 | **0.8080** |
| **F1-score** | 0.6657 | 0.7690 | **0.7921** |
| **AUC Score** | 0.6897 | 0.8521 | **0.8691** |

**Kết luận:** **Logistic Regression** là mô hình tối ưu nhất với khả năng phân tách hai lớp cảm xúc vượt trội và các chỉ số đồng đều.

## 📂 Cấu trúc Repository

* `data/`: Thư mục chứa tập dữ liệu (sau khi đã xử lý sơ bộ).
* `notebooks/`: File `.ipynb` chứa mã nguồn huấn luyện và trực quan hóa.
* `docs/`: File báo cáo chi tiết (PDF).
* `README.md`: Hướng dẫn chung.

## 🚀 Hướng dẫn chạy code

1. Clone repository:
```bash
git clone https://github.com/VietKhiem12a5/data_mining_nhom7_HK251

```


2. Cài đặt thư viện cần thiết: `pip install pandas scikit-learn nltk matplotlib seaborn`.
3. Chạy các cell trong notebook để xem kết quả tiền xử lý và huấn luyện mô hình.

---

**Giảng viên hướng dẫn:** Đỗ Thanh Thái.
