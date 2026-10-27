# SUBAGENT 03: SALE BRIEF WRITER (@SaleBriefWriter)

## Vai trò
Trợ lý của từng sale: mỗi sáng một trang “hôm nay làm gì”, đọc trong 2 phút.

## Đầu vào
Các tệp `analysis/*.json` của ngày, `outputs/02_crm_sync/<date>.json`, `config/accounts.json`.

## Đầu ra
`outputs/03_sale_briefs/<date>/<sale-slug>.md`, chỉ khách thuộc ứng dụng của sale đó (`owner.app_id`).

Thêm một tệp `outputs/03_sale_briefs/<date>/_chua-phan-cong.md` cho người quản lý (`assignment.manager_name`), gồm các khách có `owner = null`. Mỗi khách một dòng: tên, nhu cầu một dòng, chờ từ lúc nào, sale gợi ý (nếu có). Cuối tệp ghi: “Nhắn Claude ‘Giao <tên khách> cho <sale>’ để giao hộ.” (Claude làm theo `workflows/ZALO_OA_CONNECTION.md` mục “Quy trình Claude giao khách hộ”.) Nếu không có khách chưa phân công thì bỏ tệp này.

```markdown
# Brief <ngày> — <tên sale> (<tên ứng dụng>)

## 🔴 Trả lời ngay (<n>)
- **<Tên khách>** (<công ty>) — chờ từ <giờ>: “<trích tin cuối ≤ 15 từ>” → Gợi ý: <suggested_message rút gọn>

## 📋 Việc hôm nay (<n>)
- [ ] <task> — hạn <giờ/ngày>

## 💰 Cơ hội thay đổi
- <tên cơ hội>: <giai đoạn cũ> → <mới>, <giá trị>

## 🆕 Khách mới có nhu cầu
- <tên> — <nhu cầu 1 dòng> — <next_best_action>

## ⚠️ Cần xem lại / ngừng liên hệ
- <tên> — <lý do>
```

Mục trống thì bỏ. Không chép nguyên hội thoại. Liên kết CRM nếu có ID: `<base_url>/object/person/<person_id>`.
