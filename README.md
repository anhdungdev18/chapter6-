# Chapter 6: Xây Dựng Inverted Index Và Hệ Tìm Kiếm Văn Bản

## 1. Bài Toán

Đầu vào của bài toán là:

- một thư mục chứa nhiều tài liệu `.txt`
- một `StopList`

Mục tiêu:

- tạo `inverted index`
- tìm tài liệu theo 1 từ
- tìm theo nhiều từ có trọng số
- tìm theo cụm từ
- tìm theo biểu thức `AND / OR / NOT`
- lưu chỉ mục ra file JSON

## 2. Ý Tưởng Chung

```text
Tài liệu văn bản
    ->
Tokenize + Normalize + Remove StopWords
    ->
Inverted Index
    ->
Tìm kiếm và xếp hạng kết quả
```

Ý chính:

- văn bản thô được tiền xử lý
- dữ liệu được đưa vào chỉ mục đảo
- khi truy vấn, hệ thống tra cứu trên index thay vì quét lại toàn bộ file

## 3. Biểu Diễn Dữ Liệu

Các thành phần chính trong code:

- `IndexedDocument`
  - lưu thông tin từng tài liệu
- `InvertedIndexData`
  - lưu toàn bộ chỉ mục
- `doc_table`
  - bảng tài liệu
- `term_table`
  - danh sách term
- `inverted_index`
  - term -> postings list
- `doc_frequencies`
  - số tài liệu chứa term
- `document_count`
  - tổng số tài liệu

## 4. Cấu Trúc Inverted Index

Chỉ mục đảo có dạng:

```text
term -> postings list
```

Trong đó:

- `term` là từ khóa sau tiền xử lý
- `postings list` là danh sách tài liệu chứa từ đó

Mỗi posting gồm:

- tên tài liệu
- số lần xuất hiện

Ví dụ:

```text
cars -> {doc1.txt: 2, doc3.txt: 1}
city -> {doc1.txt: 1, doc2.txt: 1}
```

## 5. Xây Dựng Inverted Index

Phần này nằm trong `6A.py`.

Các bước:

1. Đọc `StopList`
2. Duyệt từng file văn bản
3. Tokenize nội dung
4. Normalize token
5. Loại bỏ stop words
6. Cập nhật `inverted_index`
7. Tính `doc_frequencies`
8. Tạo `term_table`

## 6. Tiền Xử Lý

Hệ thống hiện tại đã cải thiện:

- tokenize theo regex Unicode
- normalize bằng `unicodedata.normalize(...).casefold()`
- hỗ trợ lemmatization
- loại bỏ stop words

Ý nghĩa:

- xử lý từ trong tài liệu và từ truy vấn nhất quán hơn
- tăng chất lượng index
- tăng độ chính xác khi tìm kiếm

## 7. Tìm Kiếm Theo 1 Từ

Phần này nằm trong `SingleWordFinder.Find` của `6B.py`.

Cách hoạt động:

1. Nhận một từ truy vấn
2. Chuẩn hóa từ đó
3. Lấy postings từ `inverted_index`
4. Tính điểm theo:
   - tần suất xuất hiện
   - độ hiếm của từ (`IDF`)
   - trọng số người dùng nhập
5. Sắp xếp và trả về `top_n`

Scoring hiện dùng `TF-IDF`.

## 8. Tìm Kiếm Theo Nhiều Từ

Phần này nằm trong `WordFileFinder.Find` của `6C.py`.

File truy vấn có dạng:

```text
<word> <weight>
```

Các bước:

1. Đọc file truy vấn
2. Chuẩn hóa từng từ
3. Tra cứu từng từ trong `inverted_index`
4. Cộng điểm `TF-IDF` theo trọng số
5. Sắp xếp kết quả cuối

## 9. Công Thức Xếp Hạng

Hệ thống sử dụng ý tưởng:

```text
Score(document, term) = TF(term, document) x IDF(term) x Weight(term)
```

Trong đó:

- `TF`: tần suất của term trong tài liệu
- `IDF`: độ hiếm của term trong tập tài liệu
- `Weight`: trọng số do người dùng cung cấp

## 10. Phrase Search

Phần này nằm trong `AdvancedQueryFinder.FindPhrase` của `6C.py`.

Hệ thống:

- chuẩn hóa cụm từ truy vấn
- đọc token của từng tài liệu
- kiểm tra chuỗi từ liên tiếp
- đếm số lần xuất hiện
- sắp xếp kết quả

## 11. Boolean Query

Phần này nằm trong `AdvancedQueryFinder.FindBoolean` của `6C.py`.

Hệ thống hỗ trợ:

- `AND`
- `OR`
- `NOT`
- ngoặc `(` `)`

Ví dụ:

```text
cars AND city
cars OR road
cars AND NOT road
```

## 12. Giao Diện Demo

GUI nằm trong `6D.py`.

Các chức năng chính:

- chọn thư mục tài liệu
- chọn stop list
- tạo index
- lưu index ra JSON
- tìm theo 1 từ
- tìm theo WordFile
- tìm theo phrase
- tìm theo boolean query

## 13. Ưu Điểm

- tìm kiếm nhanh nhờ inverted index
- có tiền xử lý và lemmatization
- scoring cải thiện bằng TF-IDF
- hỗ trợ nhiều kiểu truy vấn
- có thể lưu index ra JSON

## 14. Hạn Chế

- dữ liệu demo còn nhỏ
- phrase search còn đơn giản
- boolean query mới ở mức cơ bản
- chưa dùng BM25

## 15. Các Tệp Chính

- `6A.py`: tạo inverted index và lưu index
- `6B.py`: tìm kiếm theo 1 từ
- `6C.py`: tìm kiếm nhiều từ, phrase và boolean query
- `6D.py`: giao diện demo

## 16. Cách Chạy

Chạy giao diện:

```powershell
python 6D.py
```

## 17. Kết Luận

Chapter 6 xây dựng một hệ tìm kiếm văn bản dựa trên `inverted index`.

Hệ thống hiện hỗ trợ:

- tìm theo 1 từ
- tìm theo nhiều từ có trọng số
- phrase search
- boolean query

Đây là nền tảng quan trọng của các hệ thống truy hồi thông tin.
