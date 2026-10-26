#!/bin/sh
# Shows a macOS dialog where the user pastes the TinaCRM API key, saves it to
# config/tinacrm_api_key.txt (gitignored). If the TinaCRM address is given, the key is saved
# only after the TinaCRM REST API accepts it. The key is never printed, so it stays out of the chat.
# Usage: sh scripts/tinacrm_save_key.sh [https://<workspace>.tinacrm.com]
dir="$(cd "$(dirname "$0")/.." && pwd)"
key_file="$dir/config/tinacrm_api_key.txt"
base_url="${1%/}"
base_url="${base_url%/mcp}"

key=$(osascript \
  -e 'activate' \
  -e 'text returned of (display dialog "Dán API key TinaCRM vào ô dưới rồi bấm Lưu." default answer "" with hidden answer with title "Kết nối TinaCRM" buttons {"Hủy", "Lưu"} default button "Lưu" cancel button "Hủy")' \
  2>/dev/null) || { echo "Đã hủy, chưa lưu khóa."; exit 1; }
key=$(printf %s "$key" | tr -d ' \r\n')
[ -n "$key" ] || { echo "Ô trống, chưa lưu khóa."; exit 1; }

if [ -n "$base_url" ]; then
  # Header passed via stdin config so the key never shows up in `ps`.
  code=$(printf 'header = "Authorization: Bearer %s"\n' "$key" | \
    curl -s -o /dev/null -w '%{http_code}' -m 20 -K - "$base_url/rest/people?limit=1")
  case "$code" in
    200) echo "TinaCRM chấp nhận khóa." ;;
    401|403) echo "TinaCRM từ chối khóa (HTTP $code): khóa sai, hết hạn hoặc đã xóa. Chưa lưu."; exit 2 ;;
    *) echo "Không kiểm tra được khóa (HTTP $code): xem lại địa chỉ TinaCRM. Chưa lưu."; exit 3 ;;
  esac
fi

umask 077
printf '%s\n' "$key" > "$key_file"
echo "Đã lưu khóa vào config/tinacrm_api_key.txt."
