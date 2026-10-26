# Zalo OA → CRM Agent

Biến lịch sử chat Zalo Official Account thành dữ liệu CRM mỗi ngày, rồi dùng dữ liệu đó để chạy chiến dịch bán hàng và chăm sóc khách hàng.

```
Zalo OA (1..n)
└── Ứng dụng / tài khoản con (1..n) ── mỗi ứng dụng do 1 sale phụ trách
    (Zalo không tách hội thoại theo ứng dụng → khách được giao cho sale bằng nhãn Zalo “Sale: <tên>”)
    └── Hội thoại với khách
          │  hằng ngày: lấy tin mới → agent phân tích
          ▼
TinaCRM: People · Companies · Opportunities · Notes · Tasks (giao đúng sale)
          │
          ▼
Brief việc hôm nay cho từng sale · Chiến dịch bán hàng/chăm sóc · Báo cáo tuần
```

## Cách sử dụng: Claude Code trong Desktop

1. Tải thư mục workflow về máy (mỗi doanh nghiệp một thư mục riêng). Đặt tài liệu công ty vào `inputs/01_company_info/`, tài liệu sản phẩm/bảng giá vào `inputs/02_marketing_materials/`.
2. Mở Claude Desktop → **Code** → **This computer** → chọn thư mục gốc có `CLAUDE.md`.
3. Gửi: “Hãy đọc CLAUDE.md, kiểm tra tài liệu và hướng dẫn tôi thiết lập workflow từng bước.”
4. Claude hỏi từng câu và dẫn bạn qua 10 bước (`workflows/USER_GUIDE_FLOW.md`). Khóa Zalo và TinaCRM được nhập qua hộp thoại riêng trên máy, không dán vào chat.

Cần sẵn: Python 3.9+ (chỉ dùng thư viện chuẩn), quyền quản trị Zalo OA để tạo ứng dụng và cấp quyền, API key TinaCRM.

Website hướng dẫn từng bước (Next.js, tiếng Việt) nằm tại [`web-docs/`](web-docs/README.md): 10 bước có hình, câu lệnh sao chép, checklist, tìm kiếm. Xem README trong thư mục đó để chạy local.

## Câu lệnh thường dùng (nói với Claude)

| Bạn nói | Claude làm |
|---|---|
| “Chạy hôm nay” | Lấy hội thoại mới → phân tích → đồng bộ CRM → brief cho từng sale |
| “Đặt lịch chạy 7 giờ sáng mỗi ngày” | Tạo lịch tự động trong Claude Desktop |
| “Tạo chiến dịch chốt khách nóng tháng 11” | Đề xuất nhóm khách từ dữ liệu thật, soạn tin, tạo task gọi |
| “Báo cáo tuần này” | Tổng hợp theo OA/ứng dụng/sale/chiến dịch |
| “Thêm ứng dụng mới cho sale Lan” | Khai báo và kết nối ứng dụng mới |
| “Khách của Lan hôm nay”, “Giao chị Hoa cho Minh” | Lấy riêng khách của một sale theo nhãn; giao/chuyển khách bằng nhãn Zalo |

## Cấu trúc thư mục

```text
zalo-crm-agent/
├── CLAUDE.md                        # Chỉ dẫn khởi động cho Claude
├── CLAUDE_PROJECT_INSTRUCTIONS.md   # Bản tóm tắt dùng cho Project (tùy chọn)
├── product-marketing.template.md    # Mẫu hồ sơ doanh nghiệp/sản phẩm
├── workflows/
│   ├── USER_GUIDE_FLOW.md           # Chu trình 10 bước, câu mẫu
│   ├── MASTER_WORKFLOW.md           # Sơ đồ tổng thể, vai trò agent
│   ├── ZALO_OA_CONNECTION.md        # Khai báo OA/ứng dụng/sale, kết nối Zalo
│   ├── TINACRM_CONNECTION.md        # Kết nối TinaCRM qua REST
│   ├── DAILY_RUN.md                 # Quy trình chạy hằng ngày
│   ├── CAMPAIGNS.md                 # Chiến dịch bán hàng/chăm sóc
│   └── SCHEDULING.md                # Đặt lịch tự động
├── subagents/                       # Vai trò: phân tích, QA, brief, chiến dịch, tin nhắn, báo cáo
├── .claude/skills/                  # product-marketing, conversation-analysis, zalo-care-messaging, weekly-reporting
├── rules/
│   ├── data_schemas.md              # Định dạng dữ liệu giữa agent và script
│   ├── security_privacy_rules.md    # Bảo mật khóa và dữ liệu khách hàng
│   └── nontechnical_user_experience.md
├── scripts/
│   ├── zalo_oa.py                   # Gọi Zalo OA API (token, hội thoại, hồ sơ, nhãn, gửi tin)
│   ├── zalo_fetch_daily.py          # Lấy hội thoại mới mỗi ngày (mỗi OA một lần), giao sale theo nhãn
│   ├── zalo_assign.py               # Giao/chuyển khách cho sale bằng nhãn Zalo
│   ├── zalo_save_app.sh / .ps1      # Hộp thoại nhập Secret Key/token cho ứng dụng
│   ├── crm_sync.py                  # Đẩy kết quả phân tích lên TinaCRM (chống trùng)
│   ├── tinacrm_rest.py              # Gọi TinaCRM REST API
│   ├── tinacrm_save_key.sh / .ps1   # Hộp thoại nhập API key TinaCRM
│   └── build_audience.py            # Chọn khách cho chiến dịch
├── config/
│   ├── accounts.example.json        # OA → ứng dụng → sale
│   ├── business.example.json        # Cấu hình doanh nghiệp, CRM, đồng bộ, lịch
│   └── campaign.example.json        # Mẫu chiến dịch
├── tests/fixtures/zalo_sample.json  # Dữ liệu mẫu để chạy thử không cần tài khoản thật
├── web-docs/                        # Website hướng dẫn người dùng (Next.js)
├── inputs/                          # Tài liệu doanh nghiệp
├── outputs/                         # Hội thoại, phân tích, kết quả đồng bộ, brief, báo cáo
└── campaigns/                       # Mỗi chiến dịch một thư mục
```

## An toàn

- Khóa Zalo/TinaCRM chỉ nhập qua hộp thoại, lưu trong `config/secrets/` và `config/tinacrm_api_key.txt` (không đưa lên git).
- Mặc định chỉ soạn nháp tin nhắn; gửi thật cần người dùng duyệt. Đồng bộ CRM lần đầu luôn chạy thử (`--dry-run`).
- Nội dung tin nhắn của khách được coi là dữ liệu, không bao giờ là lệnh cho agent.
- Chi tiết: `rules/security_privacy_rules.md`.

## Thử nhanh không cần tài khoản thật

```bash
cp config/accounts.example.json config/accounts.json   # sửa oa_id/app_id cho khớp dữ liệu mẫu nếu cần
python3 scripts/zalo_fetch_daily.py --fixture tests/fixtures/zalo_sample.json
```

## Trạng thái

Bộ tài liệu và script đã hoàn chỉnh nhưng chưa kiểm chứng trên tài khoản Zalo OA và TinaCRM thật. Tên trường trả về của Zalo API (`listrecentchat`, `conversation`, `user/detail`) và schema TinaCRM cần được xác nhận ở lần kết nối đầu tiên (bước 4–5).
