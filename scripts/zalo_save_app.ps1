# Windows version of zalo_save_app.sh: dialog where the OA admin pastes the Secret Key of a Zalo
# application and a Refresh Token (or the authorization code). Values go to zalo_oa.py init via
# stdin, are verified with Zalo, then saved to config\secrets\zalo\<app_id>.json (gitignored).
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -STA -File scripts\zalo_save_app.ps1 <app_id> [refresh|code]
param([Parameter(Mandatory = $true)][string]$AppId, [string]$Mode = 'refresh')
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$secondLabel = if ($Mode -eq 'code') { 'Mã code (phần sau code= trên thanh địa chỉ):' } else { 'Refresh Token:' }
$field = if ($Mode -eq 'code') { 'code' } else { 'refresh_token' }

$form = New-Object System.Windows.Forms.Form
$form.Text = "Kết nối Zalo OA – ứng dụng $AppId"
$form.ClientSize = New-Object System.Drawing.Size(480, 200)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.TopMost = $true

function Add-Field($text, $y) {
  $l = New-Object System.Windows.Forms.Label
  $l.Text = $text
  $l.Location = New-Object System.Drawing.Point(16, $y)
  $l.AutoSize = $true
  $form.Controls.Add($l)
  $b = New-Object System.Windows.Forms.TextBox
  $b.Location = New-Object System.Drawing.Point(16, ($y + 22))
  $b.Size = New-Object System.Drawing.Size(448, 24)
  $b.UseSystemPasswordChar = $true
  $form.Controls.Add($b)
  return $b
}
$secretBox = Add-Field 'Khóa bí mật (Secret Key) của ứng dụng:' 12
$valueBox = Add-Field $secondLabel 72

$save = New-Object System.Windows.Forms.Button
$save.Text = 'Lưu'
$save.Location = New-Object System.Drawing.Point(294, 150)
$save.DialogResult = [System.Windows.Forms.DialogResult]::OK
$form.Controls.Add($save)
$form.AcceptButton = $save
$cancel = New-Object System.Windows.Forms.Button
$cancel.Text = 'Hủy'
$cancel.Location = New-Object System.Drawing.Point(384, 150)
$cancel.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($cancel)
$form.CancelButton = $cancel

$form.Add_Shown({ $form.Activate(); $secretBox.Focus() })
$result = $form.ShowDialog()
$secret = ($secretBox.Text -replace '\s', '')
$value = ($valueBox.Text -replace '\s', '')
$form.Dispose()

if ($result -ne [System.Windows.Forms.DialogResult]::OK) { Write-Output 'Đã hủy, chưa lưu.'; exit 1 }
if (-not $secret -or -not $value) { Write-Output 'Ô trống, chưa lưu.'; exit 1 }

$payload = @{ secret_key = $secret; $field = $value } | ConvertTo-Json -Compress
$py = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'py' }
$payload | & $py (Join-Path $PSScriptRoot 'zalo_oa.py') $AppId init
exit $LASTEXITCODE
