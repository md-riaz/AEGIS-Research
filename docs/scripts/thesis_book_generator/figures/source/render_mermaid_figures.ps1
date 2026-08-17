$ErrorActionPreference = "Stop"

$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$figuresDir = Split-Path -Parent $sourceDir
$repoRoot = Resolve-Path (Join-Path $sourceDir "..\..\..\..\..")
$pnpm = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\bin\fallback\pnpm.cmd"
$puppeteerConfig = Join-Path $sourceDir "puppeteer-config.json"

$items = @(
  @{ Input = "figure-01-dsr-workflow.mmd"; Output = "mermaid-figure-01-dsr-workflow.png"; Width = 1800; Height = 900 },
  @{ Input = "figure-03-architecture-pipeline.mmd"; Output = "mermaid-figure-03-architecture-pipeline.png"; Width = 1800; Height = 1250 },
  @{ Input = "figure-04-semantic-layer-modularity.mmd"; Output = "mermaid-figure-04-semantic-layer-modularity.png"; Width = 1500; Height = 1250 },
  @{ Input = "figure-05-vocabulary-injection.mmd"; Output = "mermaid-figure-05-vocabulary-injection.png"; Width = 1400; Height = 1200 },
  @{ Input = "figure-06-pattern-taxonomy.mmd"; Output = "mermaid-figure-06-pattern-taxonomy.png"; Width = 1800; Height = 1000 },
  @{ Input = "figure-07-sql-safety-defense.mmd"; Output = "mermaid-figure-07-sql-safety-defense.png"; Width = 1800; Height = 1200 },
  @{ Input = "figure-08-widget-lifecycle.mmd"; Output = "mermaid-figure-08-widget-lifecycle.png"; Width = 1900; Height = 700 }
)

foreach ($item in $items) {
  $inputPath = Join-Path $sourceDir $item.Input
  $outputPath = Join-Path $figuresDir $item.Output
  & $pnpm dlx @mermaid-js/mermaid-cli `
    -p $puppeteerConfig `
    -i $inputPath `
    -o $outputPath `
    -b white `
    -w $item.Width `
    -H $item.Height
}

Write-Host "Rendered Mermaid figures into $figuresDir"
