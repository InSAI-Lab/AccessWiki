param(
    [ValidateSet("G1", "G2", "G3", "G4", "G5", "G6")]
    [string]$Group = "G1",
    [switch]$ValidateOnly
)
$ErrorActionPreference = "Stop"
$launcher = Join-Path $PSScriptRoot "experiments\formal_v01\AccessWiki_组别快捷启动器\AccessWiki_组别启动器.ps1"
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
    throw "启动器不存在，请完整解压 AccessWiki-demo。"
}
& $launcher -Group $Group -ValidateOnly:$ValidateOnly
