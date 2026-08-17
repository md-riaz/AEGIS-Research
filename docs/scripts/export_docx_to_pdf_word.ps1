param(
  [Parameter(Mandatory=$true)][string]$InputDocx,
  [Parameter(Mandatory=$true)][string]$OutputPdf
)
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $true
$word.DisplayAlerts = 0
try {
  $doc = $word.Documents.OpenNoRepairDialog($InputDocx, $false, $true, $false)
  $doc.ExportAsFixedFormat($OutputPdf, 17)
  $doc.Close($false)
  Write-Output "OK:$OutputPdf"
} finally {
  $word.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
