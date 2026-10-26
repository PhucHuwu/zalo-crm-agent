# Chiến dịch bán hàng và chăm sóc khách hàng

Dữ liệu hằng ngày (chỉ mục `config/state/customers.json` + TinaCRM) là nguồn để chọn khách. Mỗi chiến dịch: một nhóm khách + một mục tiêu + một kịch bản.

## Cấu trúc

```
campaigns/<slug>/
  campaign.json            mẫu: config/campaign.example.json
  progress.md
  outputs/audience.json    danh sách khách (build_audience.py)
  outputs/audience.csv     để sale mở bằng Excel
  outputs/messages/        tin nháp theo khách
  outputs/results.md       kết quả chiến dịch
```

`slug` viết thường, không dấu, nối gạch ngang (`chot-khach-nong-t11`). Người dùng nói tên bằng lời, Claude tự đặt slug.

## Loại chiến dịch gợi ý

Đề xuất dựa trên số liệu thật trong chỉ mục (đếm theo `segment`, `lifecycle_stage`, `intent`), không đề xuất nhóm đang trống.

| Loại (`type`) | Nhóm khách điển hình | Mục tiêu |
|---|---|---|
| `sales` – chốt khách nóng | `hot_lead`, `intent: high`, nhắn trong 7 ngày | Báo giá, hẹn demo, chốt |
| `sales` – đánh thức khách nguội | `warm_lead`/`cold_lead`, im lặng > 14 ngày | Ưu đãi, nội dung hữu ích |
| `upsell` – bán thêm | `customer`/`repeat_customer`, `interests` khớp sản phẩm mới | Giới thiệu sản phẩm liên quan |
| `care` – chăm sóc sau bán | `new_customer` trong 30 ngày | Hướng dẫn dùng, xin đánh giá |
| `retention` – giữ chân | `churn_risk`, `complaint` | Sale gọi trực tiếp, xử lý vấn đề |

## Tạo chiến dịch (bước 8)

1. Hỏi mục tiêu (lựa chọn đánh số từ bảng trên, chỉ những loại có khách).
2. Đề xuất bộ lọc `audience` cụ thể, chạy `python3 scripts/build_audience.py <slug> --dry-run` để báo quy mô theo sale và số khách còn trong khung nhắn tự do. Điều chỉnh tới khi người dùng chọn “1. Dùng nhóm này”.
3. Chạy thật (không `--dry-run`), đặt `status: "ready"`.
4. Ghi chiến dịch lên CRM nếu workspace có trường chiến dịch (`crm_campaign_value`), hoặc tạo note trên từng người. Hỏi trước khi ghi hàng loạt.

## Kịch bản và cách gửi (bước 9)

Theo skill `zalo-care-messaging`.

- **Khách còn trong khung nhắn tự do** (`zalo_window: true`): soạn tin cá nhân hóa, lưu `outputs/messages/<conversation_key>.md`. Gửi qua `scripts/zalo_oa.py <owner_app_id> send-text <user_id> '<text>' --confirm` **bằng ứng dụng của đúng sale phụ trách**, chỉ khi `approval` cho phép:
  - `draft_only` (mặc định): chỉ soạn; sale tự gửi trong Zalo OA hoặc người dùng duyệt từng lô rồi mới gửi.
  - `approved_batch`: người dùng đã duyệt mẫu và danh sách; gửi trong giới hạn `daily_send_limit`.
- **Khách ngoài khung**: tạo task cho sale trên TinaCRM (“Gọi/nhắn cho … – <mục tiêu>”, kèm gợi ý nội dung) qua `scripts/tinacrm_rest.py create-task`. Không gửi tin tự do. Gửi ZNS chỉ khi doanh nghiệp đã đăng ký mẫu và kết nối riêng (ngoài phạm vi mặc định).
- Trước lần gửi thật đầu tiên: trình bày người nhận, nội dung, phạm vi; hỏi “1. Gửi như vậy. 2. Chỉnh nội dung. 3. Chưa gửi.”

## Theo dõi

Lần chạy hằng ngày sau đó tự phân tích phản hồi của khách trong chiến dịch (hội thoại mới). Khi chạy chiến dịch, đọc phân tích mới nhất của từng khách trong `audience.json` để cập nhật `outputs/results.md`: đã gửi, đã trả lời, tích cực, cơ hội tạo mới, yêu cầu ngừng liên hệ. Khách yêu cầu ngừng → loại khỏi mọi chiến dịch (chỉ mục đã đánh dấu `do_not_contact`).

## Quy tắc

- Một khách chỉ ở một chiến dịch đang `running` (`build_audience.py` tự loại).
- Mỗi phiên làm một chiến dịch, chỉ ghi vào `campaigns/<slug>/`.
- Tin gửi đi phải từ ứng dụng của sale đang phụ trách khách đó; không dùng ứng dụng khác.
- Tôn trọng giới hạn gửi của Zalo; dừng ngay khi gặp lỗi chính sách/quota và báo người dùng.
