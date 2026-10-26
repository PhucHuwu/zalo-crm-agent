# Windows version of tinacrm_save_key.sh: shows a dialog where the user pastes the TinaCRM
# API key. If the TinaCRM address is given, the key is saved only after the TinaCRM REST API
# accepts it.
# The key is never printed, so it stays out of the chat.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -STA -File scripts\tinacrm_save_key.ps1 [https://<workspace>.tinacrm.com]
param([string]$BaseUrl = '')
$BaseUrl = $BaseUrl.TrimEnd('/') -replace '/mcp$', ''
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$keyFile = Join-Path $PSScriptRoot '..\config\tinacrm_api_key.txt'

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Kết nối TinaCRM'
$form.ClientSize = New-Object System.Drawing.Size(460, 140)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.TopMost = $true

$label = New-Object System.Windows.Forms.Label
$label.Text = 'Dán API key TinaCRM vào ô dưới rồi bấm Lưu.'
$label.Location = New-Object System.Drawing.Point(16, 16)
$label.AutoSize = $true
$form.Controls.Add($label)

$box = New-Object System.Windows.Forms.TextBox
$box.Location = New-Object System.Drawing.Point(16, 48)
$box.Size = New-Object System.Drawing.Size(428, 24)
$box.UseSystemPasswordChar = $true
$form.Controls.Add($box)

$save = New-Object System.Windows.Forms.Button
$save.Text = 'Lưu'
$save.Location = New-Object System.Drawing.Point(274, 96)
$save.DialogResult = [System.Windows.Forms.DialogResult]::OK
$form.Controls.Add($save)
$form.AcceptButton = $save

$cancel = New-Object System.Windows.Forms.Button
$cancel.Text = 'Hủy'
$cancel.Location = New-Object System.Drawing.Point(364, 96)
$cancel.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.Controls.Add($cancel)
$form.CancelButton = $cancel

$form.Add_Shown({ $form.Activate(); $box.Focus() })
$result = $form.ShowDialog()
$key = ($box.Text -replace '\s', '')
$form.Dispose()

if ($result -ne [System.Windows.Forms.DialogResult]::OK) { Write-Output 'Đã hủy, chưa lưu khóa.'; exit 1 }
if (-not $key) { Write-Output 'Ô trống, chưa lưu khóa.'; exit 1 }

if ($BaseUrl) {
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
  $headers = @{ Authorization = "Bearer $key" }
  $code = 0
  try {
    $resp = Invoke-WebRequest -Uri "$BaseUrl/rest/people?limit=1" -Method Get -Headers $headers -UseBasicParsing -TimeoutSec 20
    $code = [int]$resp.StatusCode
  } catch {
    if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
  }
  if ($code -eq 200) {
    Write-Output 'TinaCRM chấp nhận khóa.'
  } elseif ($code -eq 401 -or $code -eq 403) {
    Write-Output "TinaCRM từ chối khóa (HTTP $code): khóa sai, hết hạn hoặc đã xóa. Chưa lưu."
    exit 2
  } else {
    Write-Output "Không kiểm tra được khóa (HTTP $code): xem lại địa chỉ TinaCRM. Chưa lưu."
    exit 3
  }
}

Set-Content -Path $keyFile -Value $key -Encoding ASCII
Write-Output 'Đã lưu khóa vào config\tinacrm_api_key.txt.'
