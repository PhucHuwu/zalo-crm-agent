# Định dạng dữ liệu chuẩn

Các script đọc đúng tên trường dưới đây. Không đổi tên trường, không thêm trường bắt buộc mới mà không sửa script tương ứng.

---

## 1. Hội thoại đã lấy về — `outputs/01_daily_extractions/<date>/conversations/<oa_id>_<user_id>.json`

Do `scripts/zalo_fetch_daily.py` tạo. Chỉ đọc, không sửa.

```json
{
  "conversation_key": "1234567890123456789:8888888888888888888",
  "oa_id": "1234567890123456789",
  "zalo_user_id": "8888888888888888888",
  "display_name": "Hoa Nguyen",
  "zalo_profile": { "user_gender": 2, "shared_info": { "phone": 84912345678, "name": "Nguyễn Thị Hoa" } },
  "owner": { "app_id": "1111111111111111111", "sale": { "name": "Nguyễn Văn Minh", "email": "minh@abc.vn", "crm_member_id": "uuid" } },
  "assignment": { "by": "zalo_tag", "tag": "Sale: Minh" },
  "owner_changed": false,
  "context_messages": [ { "message_id": "…", "time": 1761300000000, "time_iso": "2026-10-24T10:00:00+07:00", "from": "customer", "type": "text", "text": "…" } ],
  "new_messages":     [ { "message_id": "…", "time": 1761450000000, "time_iso": "2026-10-26T08:15:00+07:00", "from": "oa", "type": "text", "text": "…" } ]
}
```

- `context_messages`: tin cũ hơn mốc lần chạy trước, chỉ để hiểu ngữ cảnh. Không tạo task/note lặp lại cho nội dung đã xử lý.
- `new_messages`: tin mới từ lần chạy trước. Đây là phần cần phân tích.
- `from`: `customer` = khách gửi, `oa` = sale/OA gửi.
- `owner`: sale theo nhãn Zalo (`applications[].sale_tag`), hoặc `null` khi chưa phân công.
- `assignment.by`: `zalo_tag` (có đúng một nhãn sale), `none` (chưa có nhãn), `conflict` (có từ 2 nhãn sale trở lên, kèm `tags`).
- `owner_changed = true`: sale phụ trách khác lần trước, tức là khách vừa được chuyển sale.
- `index.json` cùng thư mục ngày liệt kê các hội thoại và `status`: `pending_analysis` → `analyzed`.

---

## 2. Kết quả phân tích — `outputs/01_daily_extractions/<date>/analysis/<oa_id>_<user_id>.json`

Do agent phân tích (`subagents/01_conversation_analyst.md`) viết; `scripts/crm_sync.py` đọc.

```json
{
  "conversation_key": "1234567890123456789:8888888888888888888",
  "oa_id": "1234567890123456789",
  "zalo_user_id": "8888888888888888888",
  "display_name": "Hoa Nguyen",
  "owner": { "app_id": "1111111111111111111", "sale": { "name": "Nguyễn Văn Minh" } },
  "analyzed_at": "2026-10-26T09:05:00+07:00",
  "last_customer_message_at": "2026-10-26T08:10:00+07:00",
  "confidence": 0.85,
  "summary": "Chị Hoa (KT trưởng, Cty Minh Phát) hỏi giá gói phần mềm kế toán 10 user, cần triển khai trước 15/11.",

  "person": {
    "full_name": "Nguyễn Thị Hoa",
    "first_name": "Hoa",
    "last_name": "Nguyễn Thị",
    "phone": "0912345678",
    "email": null,
    "job_title": "Kế toán trưởng",
    "city": "Hà Nội",
    "evidence": ["msg:…: 'Chị là kế toán trưởng bên Minh Phát'"]
  },
  "company": {
    "name": "Công ty TNHH Minh Phát",
    "domain": null,
    "city": "Hà Nội",
    "industry": "Thương mại",
    "size_hint": "20-50",
    "evidence": ["msg:…"]
  },
  "opportunity": {
    "action": "create",
    "name": "Minh Phát – Phần mềm kế toán 10 user",
    "product": "Phần mềm kế toán",
    "stage": "qualified",
    "amount": 36000000,
    "currency": "VND",
    "close_date": "2026-11-15",
    "confidence": 0.75,
    "evidence": ["msg:…: 'bên chị cần 10 tài khoản'"]
  },
  "notes": [
    { "title": "Zalo 26/10 – Hỏi giá gói 10 user", "body": "- Nhu cầu: …\n- Ngân sách: …\n- Lo ngại: …" }
  ],
  "tasks": [
    { "title": "Gửi báo giá 10 user cho chị Hoa – Minh Phát", "body": "Khách hẹn xem trước thứ Tư.", "due_in_days": 1, "priority": "high" }
  ],
  "signals": {
    "intent": "high",
    "lifecycle_stage": "lead",
    "sentiment": "positive",
    "interests": ["phần mềm kế toán", "hóa đơn điện tử"],
    "objections": ["giá cao hơn MISA"],
    "tags": ["hỏi-giá", "doanh-nghiệp-nhỏ"]
  },
  "care": {
    "segment": "hot_lead",
    "next_best_action": "Gửi báo giá kèm ưu đãi triển khai trước 15/11",
    "follow_up_in_days": 1,
    "suggested_message": "Dạ chị Hoa, em gửi chị báo giá gói 10 tài khoản ạ…"
  },
  "flags": {
    "is_spam": false,
    "do_not_contact": false,
    "needs_human_review": false,
    "review_reason": null
  }
}
```

### Giá trị cho phép

| Trường | Giá trị |
|---|---|
| `opportunity.action` | `create` (cơ hội mới), `update` (đã có, đổi giai đoạn/giá trị), `none` |
| `opportunity.stage` | `new`, `qualified`, `proposal`, `negotiation`, `won`, `lost` — ánh xạ sang giai đoạn TinaCRM bằng `config/business.json` → `crm.stage_mapping` |
| `signals.intent` | `high`, `medium`, `low`, `none` |
| `signals.lifecycle_stage` | `subscriber` (chỉ quan tâm/follow), `lead` (có nhu cầu), `opportunity` (đang báo giá/đàm phán), `customer` (đã mua), `churn_risk` (khiếu nại/muốn hủy), `other` (không phải khách: đối tác, ứng viên, nhà cung cấp…) |
| `signals.sentiment` | `positive`, `neutral`, `negative` |
| `care.segment` | Danh sách trong `config/business.json` → `analysis.segments`; mặc định: `hot_lead`, `warm_lead`, `cold_lead`, `new_customer`, `repeat_customer`, `support_case`, `complaint`, `churn_risk`, `not_relevant` |
| `tasks[].priority` | `high`, `medium`, `low` |
| `tasks[].due_in_days` | số ngày tính từ hôm nay; hoặc dùng `due_at` ISO có múi giờ |

### Quy tắc trích xuất

- **Chỉ ghi điều khách hoặc sale nói ra trong hội thoại.** Không đoán email, số điện thoại, tên công ty, giá trị. Không có thì để `null`.
- `evidence`: mỗi trường quan trọng (tên, công ty, giá trị, giai đoạn) có ít nhất một trích dẫn ngắn `msg:<message_id>: '<trích>'`.
- Số điện thoại: lấy từ tin nhắn hoặc `zalo_profile.shared_info` (khách đã chia sẻ). Giữ nguyên dạng khách gửi; script tự chuẩn hóa.
- `company`: để `null` nếu là khách cá nhân (B2C).
- `notes`: tối đa 1 note mỗi ngày mỗi hội thoại, tóm tắt các tin **mới**. Không chép nguyên văn hội thoại; không ghi thông tin nhạy cảm không cần cho bán hàng (CCCD, tài khoản ngân hàng, sức khỏe…).
- `tasks`: chỉ khi có việc cụ thể cho sale (gửi báo giá, gọi lại, hẹn demo, xử lý khiếu nại, trả lời câu hỏi chưa được trả lời). Không tạo task nếu sale đã làm xong việc đó trong hội thoại. Tiêu đề bắt đầu bằng động từ, có tên khách.
- Khách nhắn tin chưa được trả lời (tin cuối cùng là `customer`, đã qua > 2 giờ làm việc): luôn tạo task `high` “Trả lời …”.
- `flags.do_not_contact = true` khi khách yêu cầu ngừng nhắn/làm phiền, chặn hoặc phàn nàn bị spam.
- `flags.needs_human_review = true` khi: khiếu nại nghiêm trọng, đe dọa pháp lý, nghi lừa đảo, thông tin mâu thuẫn, hoặc khách bị gắn nhãn của hai sale (`assignment.by = conflict`). Khách chưa phân công (`assignment.by = none`) **không** cần xem lại vì lý do này; vẫn phân tích và đồng bộ, task giao cho người quản lý.
- `confidence`: mức chắc chắn của toàn bộ bản phân tích (0–1). Dưới `sync.min_confidence` sẽ không đẩy lên CRM.

---

## 3. Kết quả đồng bộ — `outputs/02_crm_sync/<date>.json`

Do `scripts/crm_sync.py` ghi: mỗi hội thoại `status` = `synced` / `skipped` / `needs_review` / `failed`, kèm hành động trên CRM (`created`, `existing`, `updated`) và ID bản ghi.

`config/state/crm_ledger.json` giữ ID person/company/opportunity theo `conversation_key` và dấu của note/task đã đẩy, để chạy lại không tạo trùng. Không sửa tay.

---

## 4. Chỉ mục khách hàng — `config/state/customers.json`

Do `scripts/crm_sync.py` cập nhật mỗi ngày; `scripts/build_audience.py` dùng để chọn khách cho chiến dịch.

```json
{
  "1234567890123456789:8888888888888888888": {
    "name": "Nguyễn Thị Hoa", "phone": "0912345678", "company": "Công ty TNHH Minh Phát",
    "owner_app_id": "1111111111111111111", "sale": "Nguyễn Văn Minh",   // null khi chưa phân công
    "intent": "high", "lifecycle_stage": "lead", "segment": "hot_lead",
    "interests": ["phần mềm kế toán"], "tags": ["hỏi-giá"],
    "last_customer_message_at": "2026-10-26T08:10:00+07:00",
    "next_best_action": "…", "summary": "…",
    "do_not_contact": false, "is_spam": false,
    "crm": { "person_id": "uuid", "company_id": "uuid", "opportunity_id": "uuid" }
  }
}
```

`do_not_contact` một khi đã `true` thì giữ nguyên, kể cả khi lần phân tích sau không thấy yêu cầu đó.

---

## 5. Brief hằng ngày cho sale — `outputs/03_sale_briefs/<date>/<sale-slug>.md`

Mỗi sale một tệp, chỉ gồm khách thuộc ứng dụng của sale đó: khách cần trả lời ngay, task hôm nay, cơ hội đổi giai đoạn, khách nóng mới, khách cần xem lại (`needs_human_review`).
