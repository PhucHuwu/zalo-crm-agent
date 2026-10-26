# Đặt lịch chạy tự động

Claude tự tạo scheduled task cục bộ của Claude Desktop trong phiên; người dùng chỉ trả lời giờ chạy và cách duyệt.

## Điều kiện

- Đã xong bước 6 (một lần chạy tay thành công, người dùng hài lòng với chất lượng phân tích).
- Phiên có công cụ quản lý scheduled task. Không có: “Máy này chưa cho Claude tự đặt lịch. 1. Mỗi ngày tôi tự gửi ‘Chạy hôm nay’. 2. Tôi cập nhật Claude Desktop rồi thử lại.”

## Hỏi (từng câu)

1. **Giờ chạy:** “1. 7:30 sáng các ngày trong tuần, để sale có brief đầu ngày (nên chọn). 2. 7:30 sáng và 13:30 chiều. 3. Giờ khác.”
2. **Đồng bộ CRM:** “1. Tự đẩy lên CRM, khách cần xem lại thì chờ tôi (nên chọn sau khi đã chạy thử ổn). 2. Chỉ chuẩn bị, tôi duyệt rồi mới đẩy.” → `sync.auto_sync` true/false.

## Tạo lịch

- Liệt kê lịch hiện có; đã có thì sửa, không tạo trùng.
- Tên: `zalo-crm-<slug doanh nghiệp>-hang-ngay`; báo cáo tuần: `zalo-crm-<slug doanh nghiệp>-bao-cao-tuan`.
- Chạy trên máy này, đúng thư mục workflow, không bật worktree (thư mục worktree không có khóa và trạng thái).
- Câu lệnh:

  ```text
  Chạy hôm nay. Đây là lần chạy theo lịch: không có ai trả lời câu hỏi.
  Làm theo workflows/DAILY_RUN.md (mục “Khi chạy theo lịch”).
  ```

- Lưu vào `config/business.json` → `schedule` (`daily_run_time`, `days`, `task_name`, `timezone`, `execution_method = "claude_desktop_scheduled_task"`).
- Chỉ báo “đã đặt lịch” khi công cụ trả về thành công (tên lịch, lần chạy kế tiếp).

## Nhắc người dùng

- Lịch chỉ chạy khi máy bật, không ngủ và Claude Desktop đang mở; bỏ lỡ thì chạy bù khi mở lại. Con trỏ theo từng ứng dụng nên không mất tin.
- Không chạy cùng ứng dụng Zalo ở máy khác (refresh token dùng một lần).
- Lần đầu ứng dụng có thể hỏi quyền chạy lệnh: bấm **Always allow** cho đúng các lệnh `python3 scripts/...` của workflow.
