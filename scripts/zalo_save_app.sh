#!/bin/sh
# Shows macOS dialogs where the OA admin pastes the Secret Key of a Zalo application and either
# a Refresh Token (from the API Explorer) or the authorization code (from the redirect after
# opening the auth-url link). Values go straight to scripts/zalo_oa.py init via stdin, are
# verified with Zalo, then saved to config/secrets/zalo/<app_id>.json (gitignored).
# Nothing is printed, so secrets stay out of the chat.
# Usage: sh scripts/zalo_save_app.sh <app_id> [refresh|code]
dir="$(cd "$(dirname "$0")/.." && pwd)"
app_id="$1"
mode="${2:-refresh}"
[ -n "$app_id" ] || { echo "Thiếu app_id."; exit 1; }

ask() {
  osascript \
    -e 'activate' \
    -e "text returned of (display dialog \"$1\" default answer \"\" with hidden answer with title \"Kết nối Zalo OA – ứng dụng $app_id\" buttons {\"Hủy\", \"Tiếp\"} default button \"Tiếp\" cancel button \"Hủy\")" \
    2>/dev/null
}

secret=$(ask "Dán Khóa bí mật (Secret Key) của ứng dụng $app_id rồi bấm Tiếp.") || { echo "Đã hủy, chưa lưu."; exit 1; }
secret=$(printf %s "$secret" | tr -d ' \r\n')
if [ "$mode" = "code" ]; then
  value=$(ask "Dán mã code (phần sau code= trên thanh địa chỉ sau khi cấp quyền) rồi bấm Tiếp.") || { echo "Đã hủy, chưa lưu."; exit 1; }
  field=code
else
  value=$(ask "Dán Refresh Token của ứng dụng $app_id rồi bấm Tiếp.") || { echo "Đã hủy, chưa lưu."; exit 1; }
  field=refresh_token
fi
value=$(printf %s "$value" | tr -d ' \r\n')
[ -n "$secret" ] && [ -n "$value" ] || { echo "Ô trống, chưa lưu."; exit 1; }
case "$secret$value" in
  *[\"\\]*) echo "Giá trị có ký tự lạ (dấu nháy hoặc \\), có thể đã dán nhầm. Chưa lưu."; exit 1 ;;
esac

py=python3
command -v python3 >/dev/null 2>&1 || py=python
printf '{"secret_key":"%s","%s":"%s"}' "$secret" "$field" "$value" | "$py" "$dir/scripts/zalo_oa.py" "$app_id" init
