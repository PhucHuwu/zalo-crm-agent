# Sổ tay Zalo OA → CRM (Next.js)

Website hướng dẫn tiếng Việt cho người dùng ít quen công nghệ, đi theo chu trình 10 bước trong `workflows/USER_GUIDE_FLOW.md`. Nội dung dùng chung cho mọi doanh nghiệp, không đọc dữ liệu hội thoại hay cấu hình trong repository.

## Chạy local

Yêu cầu Node.js >= 20.9 và npm. Chạy trong thư mục `web-docs`:

```bash
npm install
npm run dev
```

Mở http://localhost:3000. Build production:

```bash
npm run build
npm start
```

## Nội dung và chức năng

- 10 bước, chia 3 phần: Thiết lập lần đầu (1–5), Dùng hằng ngày (6–7), Chiến dịch & báo cáo (8–10), cùng trang Câu hỏi thường gặp. Số bước trùng với số bước Claude nói trong phiên.
- Giải thích cách giao khách cho sale bằng nhãn Zalo, kết nối Zalo/TinaCRM qua hộp thoại (không dán khóa vào chat), khung nhắn tự do 48 giờ.
- Tìm kiếm tiếng Việt có hoặc không dấu; phím tắt Ctrl/Cmd+K.
- Câu lệnh sao chép vào Claude, checklist lưu trong localStorage của trình duyệt.
- Chế độ sáng/tối, giao diện mobile, hỗ trợ in.

Sửa nội dung tại `src/lib/guides.ts`, hình tại `src/lib/visuals.ts` (khóa `"<slug>:<section id>"`). Khi đổi chu trình trong `workflows/USER_GUIDE_FLOW.md`, cập nhật cả hai nơi để số bước khớp nhau.
