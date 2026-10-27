---
name: zalo-care-messaging
description: Soạn và (khi được duyệt) gửi tin nhắn bán hàng/chăm sóc khách hàng qua Zalo OA bằng ứng dụng của đúng sale phụ trách; khách ngoài khung nhắn tự do thì tạo task gọi/nhắn trên TinaCRM. Dùng ở bước 9 (chạy chiến dịch) theo workflows/CAMPAIGNS.md.
metadata:
  version: 1.0.0
---

# Tin nhắn chăm sóc qua Zalo OA

Kỹ năng dùng bởi `@CareMessenger` (`subagents/05_care_messenger.md`). Chỉ làm việc trong `campaigns/<slug>/`.

## 1. Đầu vào

- `campaigns/<slug>/campaign.json`: `type`, `goal`, `priority_products`, `sequence_steps`, `tone`, `approval`, `daily_send_limit`.
- `campaigns/<slug>/outputs/audience.json`: danh sách khách, mỗi khách có `conversation_key`, `zalo_user_id`, `owner_app_id`, `sale`, `zalo_window`.
- Phân tích mới nhất của từng khách (`outputs/01_daily_extractions/*/analysis/<oa_id>_<user_id>.json`): `summary`, `signals`, `care.suggested_message`.
- `product-marketing.md`: lợi ích, ưu đãi, câu chữ được phép dùng.

## 2. Nguyên tắc viết

- Viết như chính sale đó đang nhắn: xưng hô giống hội thoại trước (anh/chị/em, “dạ”, “ạ”), không dùng giọng quảng cáo.
- Ngắn: 2–4 câu, tối đa ~400 ký tự. Một lời kêu gọi duy nhất (hẹn gọi, gửi báo giá, xác nhận lịch…).
- Mở đầu bằng điều khách đã nói (sản phẩm quan tâm, câu hỏi còn dở, lần mua trước). Ghi một dòng “Lý do cá nhân hóa” trong tệp nháp.
- Chỉ nêu giá, ưu đãi, cam kết có trong `product-marketing.md` hoặc `campaign.json`. Không hứa điều doanh nghiệp chưa duyệt.
- Không nhắc thông tin nhạy cảm, không nhắc chuyện khách đã khiếu nại trừ khi chiến dịch là `retention`.
- Khách `churn_risk`/`complaint`: không gửi tin tự động; luôn tạo task để sale gọi.

## 3. Đầu ra theo khách

| Trường hợp | Làm gì |
|---|---|
| `do_not_contact` hoặc `is_spam` | Bỏ qua (lẽ ra `build_audience.py` đã loại). |
| `zalo_window: true` | Tạo `outputs/messages/<conversation_key>.md` (thay `:` bằng `_` trong tên tệp): chạm 1, các chạm sau theo `sequence_steps`, lý do cá nhân hóa. |
| `zalo_window: false` | Tạo task CRM cho sale qua `scripts/tinacrm_rest.py <base_url> create-task` với `assigneeId` = `crm_member_id` của sale, `personId` từ chỉ mục; nội dung: mục tiêu, bối cảnh 2 dòng, câu mở đầu gợi ý. |

Ghi mọi khách vào `outputs/messages/_index.csv`: `conversation_key,sale,channel,status,message_id,updated_at` với `status` ∈ `draft`, `approved`, `sent`, `task_created`, `skipped`, `failed`.

## 4. Duyệt và gửi

1. Trình bày cho người dùng: số tin nháp theo sale, 3 tin mẫu, số task sẽ tạo. Hỏi:
   *“1. Duyệt tất cả. 2. Chỉnh nội dung. 3. Chỉ lưu nháp, sale tự gửi.”*
2. `approval = draft_only` → dừng ở nháp (sale tự gửi trong Zalo OA). Chỉ khi người dùng chọn rõ “gửi” và đổi `approval` thành `approved_batch` mới gửi.
3. Gửi từng tin:
   ```
   python3 scripts/zalo_oa.py <owner_app_id> send-text <zalo_user_id> '<nội dung>' --confirm
   ```
   - Luôn dùng `owner_app_id` của khách, không dùng ứng dụng khác.
   - Không vượt `daily_send_limit` (chiến dịch) và `zalo.daily_send_limit_per_app` (doanh nghiệp).
   - Kiểm tra lại khung nhắn ngay trước khi gửi nếu danh sách được tạo từ hôm trước.
   - Ghi `message_id` trả về, đổi `status` thành `sent`.
4. Lỗi quota, lỗi chính sách, lỗi ngoài khung, token hết hạn → **dừng cả lô**, báo người dùng bằng lời đời thường, không thử lại liên tục.

## 5. Sau khi gửi

- Tạo note ngắn trên CRM cho từng người đã nhận tin (nếu người dùng đồng ý ghi hàng loạt): “Chiến dịch <tên> – đã gửi tin chạm 1 ngày …”.
- Cập nhật `campaigns/<slug>/progress.md` và `outputs/results.md` (đã gửi, task đã tạo, lỗi).
- Phản hồi của khách sẽ được lần chạy hằng ngày phân tích; không đọc hội thoại riêng trong phiên chiến dịch trừ khi người dùng yêu cầu.
