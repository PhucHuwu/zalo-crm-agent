---
name: product-marketing
description: Trích xuất và tổng hợp toàn bộ định vị công ty, năng lực cốt lõi, danh mục sản phẩm/dịch vụ, đối tượng mục tiêu và điểm đau khách hàng từ tài liệu ban đầu vào file trung tâm product-marketing.md. Sử dụng ở Bước 2 của quy trình (hiểu doanh nghiệp).
metadata:
  version: 2.0.0
---

# Product Marketing Context Extractor

Kỹ năng này đóng vai trò là **Nền tảng Ngữ cảnh Trung tâm (Single Source of Truth)** cho toàn bộ quy trình. Các kỹ năng `conversation-analysis` (nhận ra sản phẩm khách hỏi, ước giá trị cơ hội), `zalo-care-messaging` (nội dung, ưu đãi được phép dùng) và `weekly-reporting` đều đọc file `product-marketing.md` do kỹ năng này tạo ra trước khi thực hiện nhiệm vụ.

## 1. Nguồn dữ liệu đầu vào
- Thư mục `inputs/01_company_info/`: Slide, Profile doanh nghiệp, PDF/DOCX giới thiệu năng lực.
- Thư mục `inputs/02_marketing_materials/`: Brochure, bảng giá, slide sản phẩm/dịch vụ, case study.

## 2. Quy trình xử lý (Bước 2)
1. **Phân tích Năng lực Doanh nghiệp:**
   - Đọc toàn bộ tài liệu trong `inputs/01_company_info/`.
   - Trích xuất: Tên công ty, ngành nghề, năng lực cốt lõi, lợi thế cạnh tranh độc nhất (USP).
2. **Phân tích Giải pháp & Tiếp thị:**
   - Đọc tài liệu trong `inputs/02_marketing_materials/`.
   - Trích xuất: Danh mục sản phẩm/dịch vụ, đối tượng hưởng lợi, nỗi đau thị trường (Pain points), giá trị chuyển đổi (Value Proposition).
3. **Tổng hợp thành file trung tâm:**
   - Xuất toàn bộ thông tin chuẩn hóa vào file `product-marketing.md` tại thư mục gốc.

## 3. Checkpoint hỏi người dùng
Trước khi lưu file, xuất trình bản tóm tắt và hỏi:
- *"Đây là bản đúc kết định vị doanh nghiệp và giải pháp sản phẩm. Bạn có muốn bổ sung hoặc nhấn mạnh thêm lợi thế cạnh tranh nào trước khi chuyển sang bước khai báo danh sách sản phẩm và nhóm khách không?"*
