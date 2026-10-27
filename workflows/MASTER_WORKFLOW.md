# MASTER WORKFLOW — Zalo OA → Agent → CRM → Chiến dịch

## Tổng quan

```mermaid
graph TD
    subgraph Nguồn
      OA1[Zalo OA 1] --> APP1[Ứng dụng A<br/>Sale Minh]
      OA1 --> APP2[Ứng dụng B<br/>Sale Lan]
      OA2[Zalo OA 2] --> APP3[Ứng dụng C<br/>Sale Hùng]
    end
    APP1 & APP2 & APP3 -->|hằng ngày<br/>zalo_fetch_daily.py| RAW[(conversations/*.json)]
    RAW --> AN[@ConversationAnalyst<br/>skill conversation-analysis]
    PM[(product-marketing.md)] --> AN
    HIST[(phân tích ngày trước<br/>customers.json)] --> AN
    AN --> QA[@DataQA]
    QA -->|crm_sync.py| CRM[(TinaCRM<br/>People · Companies · Opportunities · Notes · Tasks)]
    QA --> IDX[(customers.json)]
    CRM --> BR[@SaleBriefWriter<br/>brief mỗi sale]
    IDX --> CP[@CampaignPlanner<br/>build_audience.py]
    CP --> MSG[@CareMessenger<br/>tin nháp / task gọi]
    MSG -->|phản hồi của khách| APP1
    CRM & IDX --> REP[@WeeklyReporter]
```

## Vai trò (subagents/)

| Agent | Tệp | Việc | Đầu ra |
|---|---|---|---|
| @ConversationAnalyst | `01_conversation_analyst.md` | Đọc hội thoại, trích xuất people/company/opportunity/notes/tasks/signals | `analysis/*.json` |
| @DataQA | `02_data_qa.md` | Kiểm tra bằng chứng, chống bịa, chống trùng, gắn cờ xem lại | `analysis/*.json` đã sửa |
| @SaleBriefWriter | `03_sale_brief_writer.md` | Việc hôm nay cho từng sale | `03_sale_briefs/<date>/<sale>.md` |
| @CampaignPlanner | `04_campaign_planner.md` | Đề xuất & lọc nhóm khách cho chiến dịch | `campaigns/<slug>/` |
| @CareMessenger | `05_care_messenger.md` | Soạn tin chăm sóc cá nhân hóa, tạo task gọi | `outputs/messages/`, task CRM |
| @WeeklyReporter | `06_weekly_reporter.md` | Báo cáo tuần theo OA/ứng dụng/sale/chiến dịch | `04_weekly_reports/` |

Tệp vai trò không tự tạo subagent. Claude Code có thể giao vai trò cho subagent khi môi trường hỗ trợ; Codex chỉ tạo subagent khi người dùng yêu cầu. Mặc định trợ lý xử lý tuần tự theo từng vai trò, đọc tệp vai trò và skill tương ứng trước khi làm.

## Ánh xạ hội thoại → đối tượng CRM

| Đối tượng CRM | Lấy từ hội thoại | Khi nào tạo |
|---|---|---|
| **Person** | Tên khách tự giới thiệu / tên Zalo, SĐT khách gửi hoặc chia sẻ, email, chức danh, thành phố | Mọi hội thoại không phải spam |
| **Company** | Tên công ty/cửa hàng khách nhắc, website, địa chỉ | Khi khách mua cho tổ chức (B2B) |
| **Opportunity** | Sản phẩm quan tâm, số lượng, ngân sách, hạn cần, giai đoạn (hỏi giá → báo giá → đàm phán → chốt/mất) | Khi có nhu cầu mua cụ thể; cập nhật khi giai đoạn đổi |
| **Note** | Tóm tắt tin mới trong ngày: nhu cầu, phản đối, cam kết | Mỗi ngày có tin mới (tối đa 1) |
| **Task** | Việc sale phải làm: trả lời, gửi báo giá, gọi lại, hẹn demo, xử lý khiếu nại | Khi có việc cụ thể chưa làm |

Ngoài CRM, chỉ mục cục bộ lưu `signals` (intent, lifecycle_stage, sentiment, interests, objections, tags) và `care` (segment, next_best_action) — dùng để lọc chiến dịch.

## Thứ tự một ngày

1. Lấy hội thoại (theo con trỏ từng ứng dụng).
2. Phân tích từng hội thoại có tin mới, có ngữ cảnh lịch sử.
3. Kiểm tra chất lượng.
4. Đồng bộ CRM (dry-run/duyệt hoặc tự động).
5. Brief cho sale.
6. Tóm tắt, lưu tiến trình.

Chi tiết lệnh: `DAILY_RUN.md`. Chiến dịch: `CAMPAIGNS.md`. Báo cáo: skill `weekly-reporting`.

## Trạng thái triển khai

- Đã có: client Zalo OA (token xoay vòng, khóa chống chạy trùng), lấy hội thoại theo con trỏ, client TinaCRM (person/company/opportunity/note/task), đồng bộ có ledger chống trùng, lọc khách chiến dịch, dữ liệu mẫu để chạy thử (`tests/fixtures/`).
- Cần kiểm chứng trên tài khoản thật: tên trường trả về của endpoint Zalo (`listrecentchat`, `conversation`, `user/detail`) theo phiên bản API hiện hành; giá trị `stage` và trường tùy chỉnh của từng workspace TinaCRM.
- Ngoài phạm vi mặc định: webhook Zalo thời gian thực (cần server công khai), gửi ZNS, chạy khi máy tắt.
