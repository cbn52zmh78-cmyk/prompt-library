# Launch Grok from the Grok Projects workspace with compaction defaults.
# Usage: .\grok.ps1 [grok arguments...]
# Example: .\grok.ps1 -c
# Example: .\grok.ps1 "summarize the AI layer"

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$GrokArgs
)

$ProjectRoot = $PSScriptRoot

$env:GROK_COMPACTION_MODE = "segments"
$env:GROK_COMPACTION_DETAIL = "balanced"

& grok `
    --cwd $ProjectRoot `
    --compaction-mode segments `
    --compaction-detail balanced `
    @GrokArgs