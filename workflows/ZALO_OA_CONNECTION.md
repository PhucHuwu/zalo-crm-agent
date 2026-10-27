# Kết nối Zalo Official Account

## Khái niệm (giải thích cho người dùng bằng lời thường)

- **OA (Official Account):** trang Zalo chính thức của doanh nghiệp, khách nhắn tin vào đây.
- **Ứng dụng (tài khoản con):** tạo trên developers.zalo.me, được quản trị OA cấp quyền truy cập OA. Mỗi ứng dụng có **App ID**, **Secret Key** và cặp token riêng. Trong workflow này, mỗi ứng dụng gắn với **một sale**.
- **Quan trọng:** Zalo không chia hội thoại theo ứng dụng. Mọi ứng dụng của cùng một OA đều thấy **toàn bộ** hội thoại của OA. Vì vậy khách được giao cho sale bằng **nhãn** (tag) trên Zalo. Mỗi sale có một nhãn riêng, ví dụ “Sale: Minh”, khai báo ở `sale_tag`.
- Token truy cập sống khoảng 25 giờ; refresh token sống khoảng 3 tháng và **chỉ dùng được một lần** — mỗi lần làm mới Zalo trả refresh token mới, script tự lưu lại. Vì vậy:
  - Không dùng cùng một ứng dụng ở hai máy/hai thư mục workflow: máy kia sẽ dùng refresh token cũ và bị từ chối.
  - Nếu ứng dụng không chạy quá ~3 tháng, phải cấp quyền lại.

## Khai báo (bước 3)

Hỏi lần lượt, mỗi lượt một câu:

1. “Doanh nghiệp có mấy OA cần lấy hội thoại? 1. Một. 2. Nhiều hơn một.”
2. Với mỗi OA: tên OA (ID OA lấy tự động khi `check`, không bắt người dùng tìm).
3. Với mỗi OA: “OA này có mấy ứng dụng (tài khoản con) đã được cấp quyền?” Rồi từng ứng dụng: App ID (số trên trang ứng dụng tại developers.zalo.me — App ID không phải bí mật, có thể gửi trong chat), tên gợi nhớ.
4. Với mỗi ứng dụng: sale phụ trách (họ tên, email công ty). `crm_member_id` để trống, điền ở bước 5.
5. Với mỗi sale: tên nhãn Zalo dùng để đánh dấu khách của sale đó. Gợi ý “Sale: <tên>”, hoặc dùng nhãn doanh nghiệp đang có sẵn: chạy `python3 scripts/zalo_oa.py <app_id> tags` để xem danh sách nhãn của OA. Ghi vào `sale_tag`.
6. Người quản lý nhận khách chưa phân công: họ tên, ghi vào `assignment.manager_name` (điền `manager_crm_member_id` ở bước 5).
7. `reader_app_id` của OA: ứng dụng dùng để đọc hội thoại. Mặc định lấy ứng dụng đầu tiên; nếu ứng dụng này lỗi, script tự thử ứng dụng khác của cùng OA.

Ghi `config/accounts.json` theo `config/accounts.example.json`, trình bày bảng xác nhận:

| OA | Ứng dụng | App ID | Sale | Nhãn Zalo |
|---|---|---|---|---|

Một ứng dụng chỉ có một sale và một nhãn. Muốn giao toàn bộ khách của sale cũ cho sale mới: đổi `sale` của ứng dụng, giữ nguyên `sale_tag`. Muốn chuyển một khách: xem mục “Giao khách cho sale” bên dưới.

**Ứng dụng chưa có?** Hướng dẫn người quản trị OA (một thao tác mỗi lượt): developers.zalo.me → Tạo ứng dụng → Sản phẩm **Official Account** → liên kết OA → bật quyền **quản lý tin nhắn người dùng**, **quản lý thông tin người dùng** và **quản lý thông tin OA** (để gắn nhãn) → khai báo Callback URL (nếu dùng cách 2 dưới đây). Tên nút có thể khác theo phiên bản; nếu không chắc, nhờ người dùng chụp màn hình (che dữ liệu nhạy cảm).

## Lưu khóa (bước 4)

Hai cách lấy refresh token, hỏi: “1. Lấy bằng công cụ API Explorer của Zalo (nhanh, nên chọn). 2. Cấp quyền qua đường dẫn.”

**Cách 1 – API Explorer:** quản trị OA mở developers.zalo.me/tools/explorer → chọn ứng dụng → loại **OA Access Token** → Lấy Access Token → sao chép **Refresh Token**. Sau đó Claude chạy:

- macOS: `sh scripts/zalo_save_app.sh <app_id>`
- Windows: `powershell -NoProfile -ExecutionPolicy Bypass -STA -File scripts/zalo_save_app.ps1 <app_id>`

Nói trước: “Một hộp thoại Kết nối Zalo OA sẽ hiện ra: dán Khóa bí mật của ứng dụng, rồi dán Refresh Token, bấm Lưu.”

**Cách 2 – Đường dẫn cấp quyền (PKCE):**
1. `python3 scripts/zalo_oa.py <app_id> auth-url <callback_url_đã_khai_báo>` → đưa đường dẫn `url` cho quản trị OA mở và bấm cho phép.
2. Trình duyệt chuyển tới callback URL có `?code=...`. Người dùng chỉ cần sao chép phần sau `code=` (đến trước `&`).
3. Chạy `zalo_save_app.sh <app_id> code` (Windows: thêm `-Mode code`). Mã code hết hạn sau ~10 phút.

Script chỉ lưu khi Zalo chấp nhận; kết quả `{"ok": true, "oa_id", "oa_name"}`. Đối chiếu `oa_name` với OA người dùng khai báo; ghi `oa_id` vào `config/accounts.json` nếu chưa có. Không bao giờ `cat`/đọc tệp trong `config/secrets/`.

## Giao khách cho sale (nhãn Zalo)

Hai cách, dùng song song:

- **Sale tự gắn:** trong OA Manager (oa.zalo.me), khi nhận chat với khách mới, sale gắn nhãn của mình cho khách. Một khách chỉ nên có một nhãn sale.
- **Người quản lý nhờ Claude giao hộ** (không cần mở OA Manager). Ví dụ câu người quản lý nói: “Giao chị Hoa cho Minh”, “Khách nào chưa có sale?”, “Giao hết khách chưa phân công hỏi phần mềm kế toán cho Lan”, “Chuyển khách của Minh tên Tuấn sang Lan”.

### Quy trình Claude giao khách hộ

1. **Xác định khách.**
   - Tên/SĐT/công ty: `python3 scripts/zalo_assign.py find "<từ khóa>"`.
   - “Khách chưa phân công”: `python3 scripts/zalo_assign.py unassigned` (gồm `reason = no_tag` hoặc `conflict`, mới nhất trước).
   - Nhiều kết quả trùng tên thì cho người dùng chọn số. Không đoán.
2. **Xác định sale.** `python3 scripts/zalo_assign.py sales` để xem danh sách. Người dùng nói tên gọi (“Minh”) là đủ; script báo `ambiguous_sale` nếu khớp nhiều người → hỏi lại.
3. **Đề xuất (khi người dùng nhờ Claude chọn sale):** dựa trên sản phẩm khách hỏi, khu vực, `next_best_action` trong phân tích và số khách hiện có của từng sale. Nêu lý do một dòng cho mỗi khách. Không tự giao.
4. **Xem trước:** `python3 scripts/zalo_assign.py to "<sale>" <conversation_key> [...] --dry-run`. Trình bày bảng: khách | nhu cầu | sale hiện tại → sale mới | nhãn sẽ gỡ. Hỏi “1. Giao như trên. 2. Sửa. 3. Hủy.”
5. **Giao:** sau khi người dùng chọn 1, chạy lại cùng lệnh với `--confirm`. Script:
   - gỡ nhãn sale khác, gắn nhãn sale mới trên Zalo;
   - cập nhật `config/state/` để chiến dịch và brief dùng ngay;
   - trên TinaCRM (nếu đã kết nối và khách đã đồng bộ): chuyển các task **chưa xong** do workflow tạo sang sale mới, ghi trường `owner_sale` nếu có ánh xạ. Thêm `--no-crm` nếu người dùng chỉ muốn đổi nhãn.
6. **Báo kết quả:** số khách đã giao, số task đã chuyển, lỗi từng khách (nếu có). Nhắc: “Từ lần chạy tới, khách này nằm trong brief của <sale>.”

Không giao khách khi chạy theo lịch (không ai duyệt). Lệnh cũ một khách vẫn dùng được: `python3 scripts/zalo_assign.py <conversation_key> <app_id> --confirm`.

- **Kiểm tra nhãn:** `python3 scripts/zalo_assign.py check-tags` cho biết nhãn của từng sale đã có trên OA chưa. Trạng thái `not_created_on_oa` không phải lỗi: nhãn sẽ tự được tạo khi gắn cho khách đầu tiên.
- **Khách chưa phân công** (`owner = null`, `assignment.by = none`): lần chạy hằng ngày vẫn phân tích, và task CRM giao cho người quản lý. Tóm tắt hằng ngày liệt kê các khách này và hỏi người quản lý có muốn giao luôn không (quy trình trên).
- **Xung đột** (`assignment.by = conflict`, khách có nhãn của từ 2 sale trở lên): đánh dấu cần xem lại, rồi hỏi người dùng nên giữ sale nào.
- Ứng dụng đọc nhãn cần có quyền **quản lý thông tin người dùng**. Ứng dụng gắn hoặc gỡ nhãn cần có quyền **quản lý thông tin OA**.

## Kiểm tra

```
python3 scripts/zalo_oa.py <app_id> check
python3 scripts/zalo_oa.py <app_id> recent 0 3
```

Với `recent`, chỉ báo “đọc được N hội thoại gần nhất”, không in nội dung tin nhắn ra chat.

## Lỗi thường gặp

| Kết quả | Ý nghĩa | Việc cần làm |
|---|---|---|
| `code: missing_secret` | Ứng dụng chưa lưu khóa | Chạy hộp thoại lưu khóa |
| `code: reauthorize` | Refresh token hết hạn/đã dùng/bị thu hồi | Quản trị OA cấp lại (cách 1 hoặc 2) |
| `oauth_rejected` khi lưu | Sai Secret Key, token, hoặc code hết hạn | Kiểm tra lại, lấy token/code mới |
| `zalo_error -32` hoặc quyền | Ứng dụng chưa được cấp quyền quản lý tin nhắn | Quản trị OA bật quyền cho ứng dụng |
| `code: busy` | Phiên khác đang làm mới token | Chờ 1 phút, chạy lại |
| OA trả về khác cấu hình (`wrong_oa`) | Ứng dụng trỏ nhầm OA | Sửa `accounts.json` hoặc cấp quyền lại đúng OA |
| `missing_sale_tag` | Ứng dụng chưa khai báo nhãn | Hỏi tên nhãn, ghi vào `sale_tag` |
| Nhiều khách “chưa phân công” | Sale chưa gắn nhãn | Người quản lý nhờ Claude giao (`zalo_assign.py unassigned` → `to … --dry-run` → `--confirm`), hoặc nhắc sale gắn nhãn |
| `ambiguous_sale` / `sale_not_found` | Tên sale khớp nhiều người hoặc không có | Hỏi lại người dùng, đưa danh sách `sales` |

## Giới hạn API (đã đối chiếu tài liệu Zalo 10/2026)

- `listrecentchat` (`/v2.0/oa/listrecentchat`, `data={offset,count}`) và `conversation` (`/v2.0/oa/conversation`, `data={user_id,offset,count}`): tối đa 10 bản ghi mỗi lần gọi; script tự phân trang. **Không có tham số lọc theo ứng dụng hay nhân viên.** Tin của OA (`src = 0`) không cho biết sale nào đã nhắn.
- `user/getlist` (`/v3.0/oa/user/getlist`): lọc theo `tag_name` và `last_interaction_period` (`TODAY`, `YESTERDAY`, `L7D`, `L30D`, `YYYY_MM_DD:YYYY_MM_DD`), tối đa 50 người mỗi lần gọi và 10.000 người tổng cộng. Đây là cách duy nhất để “lấy riêng khách của một sale” (`zalo_fetch_daily.py --app <app_id>`).
- `user/detail` (`/v3.0/oa/user/detail`): trả `tags_and_notes_info.tag_names`, `shared_info`, `user_id_by_app` (ID của khách theo từng ứng dụng, khác `user_id` của OA).
- Gắn nhãn: `/v2.0/oa/tag/tagfollower`, tự tạo nhãn nếu chưa có. Gỡ nhãn: `/v2.0/oa/tag/rmfollowerfromtag`. Danh sách nhãn: `/v2.0/oa/tag/gettagsofoa`.
- Giới hạn tốc độ: 4.000 lần gọi mỗi phút cho mỗi ứng dụng (mã lỗi `-32` khi vượt), cộng thêm giới hạn theo gói OA.
- Access token sống 25 giờ. Refresh token sống 3 tháng và chỉ dùng được một lần.
- Webhook (không dùng mặc định vì cần máy chủ HTTPS chạy 24/7): sự kiện “OA gửi tin” có `app_id` (ứng dụng đã gửi qua API) và `sender.admin_id` (quản trị viên nhắn bằng OA Manager). Muốn tự động gán khách theo người trả lời thì phải dùng webhook; API lấy lịch sử không có thông tin này.
- Gửi tin tư vấn (`/v3.0/oa/message/cs`) chỉ được trong khung thời gian sau tin nhắn cuối của khách (cấu hình `zalo.free_message_window_hours`, mặc định 48). Ngoài khung cần tin mẫu ZNS (đăng ký riêng, có phí) hoặc sale tự liên hệ — chiến dịch tạo task cho sale thay vì gửi.
- Tên endpoint, mã lỗi và khung thời gian có thể đổi theo chính sách Zalo. Khi gặp lỗi lạ, đọc tài liệu developers.zalo.me hiện hành trước khi sửa script.

Tài liệu tham khảo (developers.zalo.me/docs/official-account/…): `bat-dau/kham-pha`, `bat-dau/gioi-thieu-official-account-api-va-cac-nhom-quyen`, `bat-dau/xac-thuc-va-uy-quyen-cho-ung-dung-new`, `tin-nhan/quan-ly-tin-nhan/lay-thong-tin-tin-nhan-gan-nhat`, `tin-nhan/quan-ly-tin-nhan/lay-thong-tin-tin-nhan-trong-mot-hoi-thoai`, `quan-ly/quan-ly-thong-tin-nguoi-dung/truy-xuat-danh-sach-nguoi-dung`, `quan-ly/quan-ly-thong-tin-nguoi-dung/truy-xuat-chi-tiet-nguoi-dung`, `quan-ly/quan-ly-thong-tin-nguoi-dung/gan-nhan-nguoi-dung`, `quan-ly/quan-ly-thong-tin-nguoi-dung/go-nhan-nguoi-dung`, `webhook/tin-nhan/su-kien-official-account-gui-tin-nhan-cho-nguoi-dung`, `phu-luc/gioi-han-toc-do-api`.
