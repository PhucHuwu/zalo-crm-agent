# Luồng dẫn dắt người dùng

Một chu trình **10 bước**, chia 3 phần. Dùng đúng tên này khi nói với người dùng.

- **Thiết lập lần đầu** (bước 1–5): một lần cho mỗi doanh nghiệp.
- **Dùng hằng ngày** (bước 6–7): lấy hội thoại, phân tích, đẩy CRM, brief cho sale.
- **Chiến dịch & báo cáo** (bước 8–10): dùng dữ liệu đã tích lũy để bán hàng và chăm sóc khách.

| Bước | Tên | Ai làm | Trợ lý làm | Xong khi |
|---|---|---|---|---|
| 1 | Mở workflow bằng trợ lý AI | Người dùng | Theo `ASSISTANT_SETUP.md`: chỉ chỗ bấm cho Claude Code hoặc Codex, cấp quyền chạy lệnh `scripts/`; lưu `assistant` vào `config/business.json`. | Đang mở đúng thư mục workflow trên máy (Claude: tab Code → This computer; Codex: Local, đã tin cậy thư mục). |
| 2 | Hiểu doanh nghiệp | Trợ lý | Đọc `inputs/` (hoặc hỏi từng câu / đọc website), viết `product-marketing.md` theo skill `product-marketing`, tạo `config/business.json` từ mẫu. Hỏi danh sách sản phẩm/dịch vụ và các nhóm khách (segment) muốn phân loại; lưu `analysis.products`, `analysis.segments`. | Người dùng duyệt tóm tắt, sản phẩm và nhóm khách. |
| 3 | Khai báo OA, ứng dụng và sale | Trợ lý | Theo `ZALO_OA_CONNECTION.md` mục “Khai báo”: hỏi từng OA → từng ứng dụng (app_id, tên gợi nhớ) → sale phụ trách. Tạo `config/accounts.json`. | Người dùng xác nhận bảng OA – ứng dụng – sale. |
| 4 | Kết nối Zalo | Người dùng + trợ lý | Với từng ứng dụng: kiểm tra ứng dụng đã **Đang hoạt động** (đủ điện thoại, email, icon 512×512) và quản trị OA đã cấp quyền + lấy token ở API Explorer (`ZALO_OA_CONNECTION.md`), rồi bật hộp thoại `scripts/zalo_save_app` để người quản trị OA dán Secret Key và refresh token (hoặc mã code). Chạy `zalo_oa.py <app_id> check`, đọc thử `recent 0 3` (chỉ báo số hội thoại, không đọc nội dung ra chat). | Mọi ứng dụng `check` thành công và đúng OA. |
| 5 | Kết nối TinaCRM | Người dùng + trợ lý | Theo `TINACRM_CONNECTION.md`: lưu khóa, `check`, `members` để gắn `crm_member_id` cho từng sale; đọc schema để điền `crm.field_mapping` và `crm.stage_mapping` (hỏi người dùng nếu cần tạo trường tùy chỉnh). | Đọc thử đúng workspace; mỗi sale có `crm_member_id`; giai đoạn cơ hội đã ánh xạ. |
| 6 | Chạy thử ngày đầu | Trợ lý | `DAILY_RUN.md` toàn bộ, nhưng đồng bộ CRM bằng `--dry-run` trước; cho người dùng xem 3–5 bản phân tích mẫu (đã rút gọn) và bảng sẽ tạo trên CRM. Sau khi duyệt: chạy thật. | Có số tạo mới/cập nhật/bỏ qua/lỗi thật trên CRM; người dùng hài lòng với chất lượng phân tích. |
| 7 | Chạy hằng ngày & đặt lịch | Trợ lý | `DAILY_RUN.md`; khi người dùng muốn tự động: `SCHEDULING.md` (hỏi giờ, có tự đẩy CRM hay chờ duyệt). | Lịch đã tạo thật hoặc người dùng chọn chạy tay. |
| 8 | Tạo chiến dịch | Trợ lý | Theo `CAMPAIGNS.md`: hỏi mục tiêu (bán thêm, chốt khách nóng, chăm sóc sau bán, kích hoạt khách nguội…), đề xuất bộ lọc khách dựa trên dữ liệu thật, `build_audience.py --dry-run`, duyệt, lưu. | Danh sách khách được duyệt, đã lưu. |
| 9 | Kịch bản chăm sóc | Trợ lý | Skill `zalo-care-messaging`: soạn chuỗi tin theo từng nhóm, cá nhân hóa bằng tóm tắt hội thoại; tạo task cho sale (khách ngoài khung nhắn tự do) hoặc nháp tin Zalo (trong khung). | Người dùng duyệt kịch bản và cách gửi. |
| 10 | Báo cáo tuần | Trợ lý | Skill `weekly-reporting`: tổng hợp theo OA, ứng dụng, sale, chiến dịch. Hỏi người nhận → ngày → giờ; đặt lịch. | Mẫu báo cáo được duyệt, lịch đã tạo. |

Sau bước 10, chu trình lặp lại từ bước 7; chiến dịch mới quay lại bước 8.

## Luôn nói số bước

“Xong **bước 4**. Tiếp theo là **bước 5 – kết nối TinaCRM**.” Không đọc nguyên 10 bước trừ khi người dùng hỏi.

## Câu mẫu

| Câu bắt đầu bằng… | Bước |
|---|---|
| “Đọc AGENTS.md (hoặc CLAUDE.md) và tài liệu trong inputs…” | 2 |
| “Thêm OA…”, “Thêm ứng dụng/tài khoản con…”, “Đổi sale phụ trách…” | 3 |
| “Giao khách … cho sale …”, “Khách nào chưa có sale?”, “Chuyển khách … sang …” | `ZALO_OA_CONNECTION.md` mục “Quy trình trợ lý giao khách hộ” |
| “Khách của <sale> hôm nay” | `DAILY_RUN.md` bước 1, `--app <app_id>` |
| “Kết nối Zalo…”, “Kết nối lại ứng dụng…” | 4 |
| “Kết nối TinaCRM…” | 5 |
| “Chạy hôm nay”, “Lấy hội thoại hôm nay”, “Chạy hằng ngày” | 6/7 (`DAILY_RUN.md`) |
| “Phân tích lại hội thoại của <khách>…” | 7 (chỉ hội thoại đó) |
| “Đặt lịch…”, “Tạm dừng lịch…” | 7 (`SCHEDULING.md`) |
| “Tạo chiến dịch…”, “Lọc khách…”, “Có bao nhiêu khách…” | 8 |
| “Soạn tin chăm sóc…”, “Kịch bản…” | 9 |
| “Báo cáo tuần…” | 10 |

## Mở đầu phiên

- **Có tiến trình:** tóm tắt tối đa ba dòng (ví dụ “Hôm qua: 42 hội thoại, 9 cơ hội mới, 3 khách cần xem lại”), hỏi “1. Chạy hôm nay. 2. Xem khách cần xem lại. 3. Chiến dịch. 4. Việc khác.”
- **Lần đầu:** làm bước 2. Nếu `inputs` trống: “1. Tôi đặt tài liệu vào thư mục — chỉ đường giúp tôi. 2. Tôi gửi website. 3. Hỏi tôi từng câu.”

## Lưu tiến trình

Bước 1–7 vào `config/workflow_progress.md`; bước 8–9 vào `campaigns/<slug>/progress.md`. Chỉ đánh dấu xong khi đạt “Xong khi” bằng kết quả công cụ thật.

```markdown
# Tiến trình — <tên doanh nghiệp>
Cập nhật: <ngày giờ>
- [x] Bước 3 Khai báo OA — 1 OA, 3 ứng dụng, 3 sale
- [ ] Bước 4 Kết nối Zalo — 2/3 ứng dụng OK; app 333… chờ quản trị OA
Lần chạy hằng ngày gần nhất: <ngày> — <số hội thoại>, <số đồng bộ>, <lỗi>
Đang chờ người dùng: <việc>
Bước tiếp theo: Bước N – <tên>
```
