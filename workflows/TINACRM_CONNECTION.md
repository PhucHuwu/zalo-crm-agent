# Kết nối TinaCRM (REST API)

Workflow đọc/ghi TinaCRM **chỉ qua REST API** bằng `scripts/tinacrm_rest.py` với API key. Không dùng MCP của TinaCRM.

## Thiết lập (bước 5)

1. Hỏi địa chỉ TinaCRM, ví dụ `https://<workspace>.tinacrm.com`. Ghi `crm.base_url` trong `config/business.json`.
2. Người dùng tạo API key: Settings → MCP & APIs → tab API → Create API key; Role đủ quyền đọc/ghi People, Companies, Opportunities, Tasks, Notes; nên đặt ngày hết hạn.
3. Bật hộp thoại lưu khóa:
   - macOS: `sh scripts/tinacrm_save_key.sh <base_url>`
   - Windows: `powershell -NoProfile -ExecutionPolicy Bypass -STA -File scripts/tinacrm_save_key.ps1 <base_url>`

   Nói trước: “Một hộp thoại Kết nối TinaCRM sẽ hiện ra, dán khóa vào ô và bấm Lưu.” Không nhận khóa qua chat.
4. `python3 scripts/tinacrm_rest.py <base_url> check`, rồi `get companies` để người dùng xác nhận đúng CRM. Chưa ghi dữ liệu.

## Gắn sale với nhân viên CRM

`python3 scripts/tinacrm_rest.py <base_url> members` → danh sách thành viên (id, tên, email). Ghép với `applications[].sale.email` trong `config/accounts.json`, ghi `crm_member_id`. Không ghép được (khác email) thì hỏi người dùng chọn. Task được giao cho `crm_member_id` của sale sở hữu hội thoại.

## Ánh xạ trường và giai đoạn

Đọc schema thật: `<base_url>/rest/open-api/core` (gọi bằng `tinacrm_rest.py get` hoặc curl với cùng khóa qua `-K -`, không in khóa).

- **Giai đoạn cơ hội** (`crm.stage_mapping`): đọc các giá trị của trường `stage` trên Opportunities, ghép với `new / qualified / proposal / negotiation / won / lost`. Hỏi người dùng khi không rõ. Giai đoạn để `null` thì không gửi `stage`.
- **Trường tùy chỉnh trên People** (`crm.field_mapping`), khuyến nghị có để chống trùng và lọc:
  - `zalo_user_id` (Text) — quan trọng nhất: khách Zalo thường không để lại email/điện thoại, đây là khóa chống trùng.
  - `zalo_oa_id`, `owner_sale`, `segment` (Text hoặc Select).

  Nếu workspace chưa có, hỏi: “1. Tôi tạo các trường này trong TinaCRM (hướng dẫn từng bước: Settings → Data model → People → Add field). 2. Bỏ qua, chỉ dùng số điện thoại/email.” Ghi đúng tên API của trường (camelCase, ví dụ `zaloUserId`) vào `field_mapping`. Không đoán tên trường.

  Khi không có trường `zalo_user_id`, chống trùng dựa vào `config/state/crm_ledger.json` (theo `conversation_key`) + điện thoại/email; nhắc người dùng không chạy workflow ở hai thư mục cho cùng OA.

## Lệnh

```
python3 scripts/tinacrm_rest.py <base_url> check | members
python3 scripts/tinacrm_rest.py <base_url> upsert-company     '{"name":"…","domain":"…","city":"…"}'
python3 scripts/tinacrm_rest.py <base_url> upsert-person      '{"firstName":"…","lastName":"…","phone":"…","companyId":"…","extra":{"zaloUserId":"…"},"matchField":"zaloUserId","matchValue":"…"}'
python3 scripts/tinacrm_rest.py <base_url> upsert-opportunity '{"name":"…","amount":36000000,"currency":"VND","stage":"…","companyId":"…","pointOfContactId":"…"}'
python3 scripts/tinacrm_rest.py <base_url> create-note        '{"title":"…","body":"…","personId":"…"}'
python3 scripts/tinacrm_rest.py <base_url> create-task        '{"title":"…","dueAt":"<ISO>","assigneeId":"…","personId":"…"}'
python3 scripts/tinacrm_rest.py <base_url> update <plural> <id> '<json>'
python3 scripts/tinacrm_rest.py <base_url> get <plural> '<filter>'
```

Thường không gọi tay: `scripts/crm_sync.py` gọi đúng thứ tự company → person → opportunity → note → task.

## Lỗi

- 401/403: khóa sai/hết hạn/thiếu quyền Role → tạo khóa mới, chạy lại hộp thoại.
- 400 với tên trường: sai `field_mapping` hoặc giá trị `stage` không có trong workspace → đối chiếu schema.
- Không gộp các lỗi thành “chưa cấu hình”; báo đúng nguyên nhân.
