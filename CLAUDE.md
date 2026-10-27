@AGENTS.md

## Riêng cho Claude Code

- Chỉ dẫn chính nằm ở `AGENTS.md` (dùng chung với Codex). Sửa ở đó, không sửa ở đây.
- Skills: dùng `.claude/skills/`, là bản sao của `.agents/skills/` do `python3 scripts/sync_skills.py` tạo.
- Có công cụ hỏi lựa chọn thì dùng cho các câu hỏi đánh số; nội dung lựa chọn giữ nguyên như trong tài liệu.
- Quyền chạy lệnh và đặt lịch: phần “Claude Code” trong `workflows/ASSISTANT_SETUP.md` và `workflows/SCHEDULING.md`.
