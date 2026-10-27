# Mở workflow và cấp quyền cho trợ lý (bước 1)

Workflow chạy được như nhau trên **Claude Code** (Claude Desktop) và **Codex** (ChatGPT desktop app). Người dùng chọn một trong hai; mọi bước sau dùng chung tài liệu. Tệp này chỉ ghi những chỗ thao tác khác nhau.

Khi hướng dẫn người dùng, một thao tác mỗi lượt, rồi hỏi “Bạn thấy màn hình đó chưa? 1. Rồi. 2. Chưa thấy.” Tên nút có thể khác theo phiên bản; nếu không chắc, nhờ chụp màn hình (che dữ liệu nhạy cảm).

## Claude Code

1. Mở Claude Desktop → tab **Code** → **This computer** (bản cũ ghi Local) → chọn thư mục gốc workflow (có `AGENTS.md`).
2. Lần đầu chạy lệnh, Claude hỏi quyền: bấm **Always allow** cho đúng các lệnh `python3 scripts/...`, `sh scripts/...` (Windows: `powershell ... scripts/...ps1`) của workflow.

## Codex (ChatGPT desktop app)

1. Mở ChatGPT desktop app → **Codex** → cuộc trò chuyện mới → chọn chạy trên máy này (**Local**), chọn thư mục gốc workflow. Không chọn worktree hay cloud: khóa và trạng thái chỉ có trong thư mục gốc.
2. Khi được hỏi có tin cậy thư mục không, chọn **tin cậy** (trust). Nhờ vậy Codex nạp quy tắc của workflow ở `.codex/rules/workflow.rules`, cho phép đúng các lệnh `scripts/` cần mạng và hộp thoại nhập khóa chạy mà không hỏi lại.
3. Chế độ quyền (ô bên dưới khung chat): giữ **Ask for approval** hoặc **Approve for me**. Không cần **Full access**.
4. Nếu Codex vẫn hỏi quyền một lệnh `scripts/` (ví dụ chưa tin cậy thư mục): chọn duyệt **luôn cho lệnh này** (không phải chỉ một lần), để lần chạy theo lịch không bị chặn.
5. Đã dùng Claude Code trước đó: Codex có mục **Settings → Import from Claude Code**; không bắt buộc, vì workflow đã có sẵn `AGENTS.md` và `.agents/skills/`.

Trợ lý chạy trên Codex:

- Chạy mỗi lần một lệnh đơn giản (`python3 scripts/zalo_oa.py <app_id> check`), không nối `&&`, `|`, `>`, không đặt biến môi trường trước lệnh; nếu không, quy tắc duyệt theo tiền tố không khớp và lệnh bị chặn hoặc phải hỏi.
- Lệnh bị chặn vì mạng (lỗi kiểu “Network is unreachable”, “nodename nor servname”, “Operation not permitted”) không phải lỗi khóa Zalo/TinaCRM: xin chạy lại ngoài sandbox, rồi hướng dẫn người dùng bước 2 hoặc 4 ở trên. Không kết luận “khóa sai” khi chưa có phản hồi thật từ Zalo/TinaCRM.
- Hộp thoại nhập khóa (`zalo_save_app`, `tinacrm_save_key`) mở trên màn hình người dùng. Nói trước để người dùng tìm cửa sổ; nếu không thấy, nhờ kiểm tra cửa sổ có bị che sau ChatGPT không.
- Vai trò trong `subagents/` được làm tuần tự trong cùng cuộc trò chuyện, trừ khi người dùng yêu cầu chạy song song.

## Kiểm tra nhanh sau bước 1

Trợ lý tự kiểm tra, không đọc kết quả kỹ thuật cho người dùng:

- Đọc được `AGENTS.md` và thấy các skill `product-marketing`, `conversation-analysis`, `zalo-care-messaging`, `weekly-reporting`.
- `python3 --version` chạy được (cần 3.9+). Không có: hướng dẫn cài Python, mỗi lượt một thao tác.

Lưu vào `config/business.json` → `assistant` (`"claude_code"` hoặc `"codex"`) để các bước sau, nhất là đặt lịch, hướng dẫn đúng chỗ bấm.
