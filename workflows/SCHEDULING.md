# Đặt lịch chạy tự động

Trợ lý tự tạo lịch chạy trên máy trong phiên; người dùng chỉ trả lời giờ chạy và cách duyệt. Cách tạo khác nhau giữa Claude Code và Codex (xem `config/business.json` → `assistant`); phần hỏi và câu lệnh dùng chung.

## Điều kiện

- Đã xong bước 6 (một lần chạy tay thành công, người dùng hài lòng với chất lượng phân tích).
- Phiên có công cụ tạo lịch. Không có: “Máy này chưa cho trợ lý tự đặt lịch. 1. Mỗi ngày tôi tự gửi ‘Chạy hôm nay’. 2. Hướng dẫn tôi tạo lịch bằng tay. 3. Tôi cập nhật ứng dụng rồi thử lại.” Chọn 2 → hướng dẫn từng thao tác theo mục của công cụ đang dùng bên dưới.

## Hỏi (từng câu)

1. **Giờ chạy:** “1. 7:30 sáng các ngày trong tuần, để sale có brief đầu ngày (nên chọn). 2. 7:30 sáng và 13:30 chiều. 3. Giờ khác.”
2. **Đồng bộ CRM:** “1. Tự đẩy lên CRM, khách cần xem lại thì chờ tôi (nên chọn sau khi đã chạy thử ổn). 2. Chỉ chuẩn bị, tôi duyệt rồi mới đẩy.” → `sync.auto_sync` true/false.

## Nội dung lịch (dùng chung)

- Liệt kê lịch hiện có; đã có thì sửa, không tạo trùng.
- Tên: `zalo-crm-<slug doanh nghiệp>-hang-ngay`; báo cáo tuần: `zalo-crm-<slug doanh nghiệp>-bao-cao-tuan`.
- Chạy trên máy này, đúng thư mục workflow, **không bật worktree** (thư mục worktree không có khóa và trạng thái).
- Câu lệnh hằng ngày:

  ```text
  Chạy hôm nay. Đây là lần chạy theo lịch: không có ai trả lời câu hỏi.
  Làm theo workflows/DAILY_RUN.md (mục “Khi chạy theo lịch”).
  ```

- Câu lệnh báo cáo tuần:

  ```text
  Báo cáo tuần này. Đây là lần chạy theo lịch: không có ai trả lời câu hỏi.
  Làm theo skill weekly-reporting.
  ```

- Lưu vào `config/business.json` → `schedule` (`daily_run_time`, `days`, `task_name`, `timezone`, `execution_method`).
- Chỉ báo “đã đặt lịch” khi công cụ trả về thành công (tên lịch, lần chạy kế tiếp).

## Claude Code

- Tạo scheduled task cục bộ của Claude Desktop bằng công cụ quản lý lịch trong phiên. `execution_method = "claude_desktop_scheduled_task"`.
- Nhắc người dùng: lịch chỉ chạy khi máy bật, không ngủ và Claude Desktop đang mở; bỏ lỡ thì chạy bù khi mở lại.
- Lần đầu ứng dụng có thể hỏi quyền chạy lệnh: bấm **Always allow** cho đúng các lệnh `python3 scripts/...` của workflow.

## Codex (ChatGPT desktop app)

- Tạo bằng cách nhờ chính cuộc trò chuyện Codex đang mở thư mục workflow: lịch **độc lập** (standalone, mỗi lần chạy là một cuộc trò chuyện mới), chạy **trong thư mục dự án (local)**, không dùng worktree. `execution_method = "codex_scheduled_task"`.
- Thêm `$conversation-analysis` (hằng ngày) hoặc `$weekly-reporting` (báo cáo tuần) vào cuối câu lệnh để lần chạy chắc chắn dùng đúng skill.
- Không có công cụ tạo lịch trong phiên: hướng dẫn người dùng mở mục **Scheduled** ở thanh bên ChatGPT desktop app → tạo lịch mới → chọn dự án là thư mục workflow, chế độ chạy local → dán câu lệnh ở trên → chọn giờ.
- Lịch chạy không người trông, dùng quyền mặc định của Codex (sandbox chặn mạng). Lệnh `scripts/` lấy Zalo và ghi TinaCRM chỉ chạy được khi:
  1. Thư mục workflow đã được **tin cậy** (Codex nạp `.codex/rules/workflow.rules`), hoặc
  2. Người dùng đã duyệt **luôn** cho các lệnh đó trong một lần chạy tay (Codex lưu vào `~/.codex/rules/default.rules`).
  Trước khi tạo lịch, chạy tay “Chạy hôm nay” một lần trên Codex và xác nhận không còn câu hỏi quyền nào. Không đề xuất **Full access** cho lịch.
- Nhắc người dùng: lịch chỉ chạy khi máy bật, không ngủ và ChatGPT desktop app đang mở. Kết quả mỗi lần chạy xem ở mục **Scheduled**.

## Nhắc chung

- Không chạy cùng ứng dụng Zalo ở máy khác hay bằng trợ lý khác cùng lúc (refresh token dùng một lần). Chỉ đặt lịch ở **một** công cụ: đã có lịch ở Claude thì không tạo thêm ở Codex, và ngược lại. Đổi công cụ thì xóa lịch cũ trước.
- Bỏ lỡ một lần chạy không mất tin: con trỏ theo từng ứng dụng, lần sau lấy tiếp.
