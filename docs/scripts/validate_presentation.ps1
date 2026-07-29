$pptxPath = "D:\Development\Personal\research\docs\scripts\Md_Riaz_Mid_Defense_Final_0322310105101024.pptx"
$outputDir = "D:\Development\Personal\research\docs\scripts\slides_rendered"

if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

try {
    $ppt = New-Object -ComObject PowerPoint.Application
    $pres = $ppt.Presentations.Open($pptxPath, [Microsoft.Office.Core.MsoTriState]::msoTrue, [Microsoft.Office.Core.MsoTriState]::msoFalse, [Microsoft.Office.Core.MsoTriState]::msoFalse)
    Write-Host "SUCCESS: Presentation validated and exported to $outputDir"
    $pres.Export($outputDir, "PNG", 1920, 1080)
    $pres.Close()
    $ppt.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($ppt) | Out-Null
} catch {
    Write-Host "ERROR: $_"
}
