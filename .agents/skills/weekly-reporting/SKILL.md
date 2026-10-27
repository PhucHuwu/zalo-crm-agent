---
name: weekly-reporting
description: Tổng hợp báo cáo tuần theo OA, ứng dụng và sale — lượng hội thoại, khách mới, cơ hội, task, tốc độ phản hồi, kết quả chiến dịch — từ tệp đầu ra và TinaCRM; lưu Markdown và gửi cho quản lý nếu đã kết nối. Dùng ở bước 10 của quy trình.
metadata:
  version: 3.0.0
---

# Báo cáo tuần

Kỹ năng dùng bởi `@WeeklyReporter` (`subagents/06_weekly_reporter.md`). **Chỉ dùng số đếm được từ tệp hoặc CRM.** Không có dữ liệu thì ghi “chưa đo”, không ước lượng.

## 1. Nguồn số liệu (7 ngày gần nhất, theo `sync.tz_offset`)

| Nguồn | Lấy gì |
|---|---|
| `outputs/01_daily_extractions/<date>/index.json` | Số hội thoại có tin mới theo OA/ứng dụng/sale |
| `outputs/01_daily_extractions/<date>/analysis/*.json` | Khách mới, `segment`, `intent`, `lifecycle_stage`, `objections`, `flags` |
| `outputs/02_crm_sync/<date>.json` | Person/company/opportunity tạo mới, cập nhật; note/task đã đẩy; lỗi |
| `config/state/customers.json` | Tồn khách theo segment/stage/sale |
| `campaigns/*/outputs/messages/_index.csv`, `results.md` | Tin đã gửi, task đã tạo, khách trả lời |
| TinaCRM (`tinacrm_rest.py get opportunities`, `get tasks`) | Giai đoạn cơ hội hiện tại, tổng giá trị pipeline, task quá hạn theo sale |

## 2. Chỉ số

1. **Hội thoại:** số hội thoại có tin mới; số khách mới; tỉ lệ khách thật (loại `other`, spam).
2. **Phản hồi:** số hội thoại khách chờ > 2 giờ làm việc (task “Trả lời…”); số còn tồn cuối tuần.
3. **Pipeline:** cơ hội mới, cơ hội chuyển giai đoạn, `won`/`lost`, tổng giá trị (chỉ cộng cơ hội có `amount`).
4. **Việc của sale:** task tạo mới, task quá hạn (từ CRM).
5. **Chăm sóc:** khách `complaint`/`churn_risk` mới; khách `do_not_contact` mới.
6. **Chiến dịch:** theo từng chiến dịch đang chạy: đã gửi, task tạo, đã trả lời, phản hồi tích cực, cơ hội phát sinh.
7. **Insight:** 3–5 nhu cầu/sở thích nổi bật, 3–5 phản đối hay gặp (từ `signals.objections`), đề xuất chiến dịch tuần tới.

Bảng chính chia theo **sale** (mỗi dòng một sale, kèm OA/ứng dụng), thêm dòng tổng theo OA.

## 3. Đầu ra

- `outputs/04_weekly_reports/weekly_report_<YYYY-WW>.md` (tuần ISO).
- Nếu gửi email: thêm bản HTML cùng tên `.html`. Không đưa số điện thoại, nội dung tin nhắn nguyên văn vào báo cáo; nêu tên khách chỉ ở mục “cần xử lý”.

## 4. Checkpoint hỏi người dùng (bước 10)

Lần đầu, hỏi từng câu:
1. *“Báo cáo tuần gửi cho ai? (email hoặc nhóm Zalo/Slack đã kết nối, hay chỉ lưu tệp)”* → `config/business.json` → `reporting.recipients`.
2. *“Muốn nhận vào lúc nào? Ví dụ: 8:30 sáng thứ Hai.”* → `reporting.day_of_week`, `reporting.time`.
3. Nếu muốn tự động: tạo lịch theo `workflows/SCHEDULING.md`, lưu `reporting.task_name`.

Chỉ gửi khi đã có công cụ gửi thật (connector email/Slack của Claude, hoặc plugin Gmail/Slack của ChatGPT/Codex) và người dùng đồng ý; nếu không, lưu tệp và báo đường dẫn.
