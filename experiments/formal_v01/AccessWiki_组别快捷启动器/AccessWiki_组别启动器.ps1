param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("G1", "G2", "G3", "G4", "G5", "G6")]
    [string]$Group,
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"
if (-not $ValidateOnly) { $Host.UI.RawUI.WindowTitle = "AccessWiki 研究人员启动器 - $Group" }

function Find-FormalRoot {
    $cursor = $PSScriptRoot
    for ($level = 0; $level -lt 8; $level++) {
        if (-not $cursor) { break }
        if (Test-Path (Join-Path $cursor "launch")) { return $cursor }
        foreach ($relative in @(
            "formal_v01",
            "experiments\formal_v01",
            "accesswiki_demo\experiments\formal_v01",
            "材料\accesswiki_demo\experiments\formal_v01"
        )) {
            $candidate = Join-Path $cursor $relative
            if (Test-Path (Join-Path $candidate "launch")) { return $candidate }
        }
        $parent = Split-Path -Parent $cursor
        if ($parent -eq $cursor) { break }
        $cursor = $parent
    }
    throw "找不到 formal_v01\launch。请先完整解压ZIP，再把‘AccessWiki_组别快捷启动器’文件夹放进 formal_v01 根目录。"
}

try {
    $Root = Find-FormalRoot
} catch {
    if ($ValidateOnly) { throw }
    Clear-Host
    Write-Host "启动器没有找到正式材料。" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host "`n当前启动器位置：$PSScriptRoot"
    Read-Host "按回车退出"
    exit 1
}
$LaunchDir = Join-Path $Root "launch"

$Sequences = @{
    G1 = @(@("R", "B1"), @("H", "B2"), @("O", "P"))
    G2 = @(@("R", "B1"), @("O", "P"),  @("H", "B2"))
    G3 = @(@("O", "B2"), @("H", "B1"), @("R", "P"))
    G4 = @(@("O", "B2"), @("R", "P"),  @("H", "B1"))
    G5 = @(@("H", "P"),  @("O", "B1"), @("R", "B2"))
    G6 = @(@("H", "P"),  @("R", "B2"), @("O", "B1"))
}

$ParticipantGroups = @{
    P01="G1"; P02="G2"; P03="G3"; P04="G4"; P05="G5"; P06="G6"
    P07="G1"; P08="G2"; P09="G3"; P10="G4"; P11="G5"; P12="G6"
}

$ErrorTasks = @{
    P01="O_B2_BAD"; P02="H_P_BAD"; P03="O_B2_BAD"; P04="H_P_BAD"; P05="O_B2_BAD"; P06="H_P_BAD"
    P07="H_P_BAD"; P08="O_B2_BAD"; P09="H_P_BAD"; P10="O_B2_BAD"; P11="H_P_BAD"; P12="O_B2_BAD"
}

$TopicNames = @{ R="铁路"; H="医院"; O="在线退货" }
$ConditionNames = @{ B1="原始权威网页"; B2="单主播中性音频＋Evidence HTML"; P="双主播问答音频＋Evidence HTML" }

function Read-LaunchPages {
    $pages = @()
    foreach ($file in Get-ChildItem -LiteralPath $LaunchDir -Filter "*.html" -File) {
        $raw = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 -ErrorAction Stop
        $pages += [PSCustomObject]@{
            Name = $file.Name
            FullName = $file.FullName
            SearchText = ($file.Name + "`n" + $raw).ToLowerInvariant()
        }
    }
    if ($pages.Count -eq 0) { throw "launch 文件夹里没有 HTML 页面。" }
    return $pages
}

$Pages = Read-LaunchPages

function Match-Topic([string]$text, [string]$topic) {
    switch ($topic) {
        "R" { return $text -match "rail_travel|rail|铁路|火车|高铁" }
        "H" { return $text -match "hospital_visit|hospital|outpatient|医院|就诊" }
        "O" { return $text -match "online_returns|returns|return|退货" }
    }
}

function Match-Condition([string]$text, [string]$condition) {
    switch ($condition) {
        "B1" { return $text -match "b1_sources|primary|(^|[^a-z0-9])b1([^a-z0-9]|$)|原始权威|原始来源" }
        "B2" { return $text -match "neutral|single|(^|[^a-z0-9])b2([^a-z0-9]|$)|单主播|中性" }
        "P"  { return $text -match "conversational|dialogue|podcast|双主播|问答" }
    }
}

function Is-Incorrect([string]$text) {
    return $text -match "incorrect|inconsisten|(^|[^a-z])error([^a-z]|$)|错误版本|不一致"
}

function Resolve-Page([string]$topic, [string]$condition, [bool]$incorrect) {
    $matches = @($Pages | Where-Object {
        (Match-Topic $_.SearchText $topic) -and
        (Match-Condition $_.SearchText $condition) -and
        ((Is-Incorrect $_.SearchText) -eq $incorrect)
    })
    if ($matches.Count -ne 1) {
        $kind = if ($incorrect) { "错误任务" } else { "正式任务" }
        $names = if ($matches.Count) { ($matches.Name -join ", ") } else { "无" }
        throw "$kind $topic-$condition 应匹配1个启动页，实际匹配$($matches.Count)个：$names"
    }
    return $matches[0]
}

function Resolve-PracticePage {
    $matches = @($Pages | Where-Object { $_.SearchText -match "bus_travel|bus|公交" -and $_.SearchText -match "practice|练习" })
    if ($matches.Count -eq 1) { return $matches[0] }
    $fallback = @($Pages | Where-Object { $_.SearchText -match "bus_travel|公交" })
    if ($fallback.Count -eq 1) { return $fallback[0] }
    throw "公交练习页无法唯一识别。当前匹配：$(($matches.Name + $fallback.Name | Select-Object -Unique) -join ', ')"
}

function Resolve-All {
    $resolved = @{}
    foreach ($topic in @("R", "H", "O")) {
        foreach ($condition in @("B1", "B2", "P")) {
            $key = "${topic}_${condition}"
            $resolved[$key] = Resolve-Page $topic $condition $false
        }
    }
    $resolved["H_P_BAD"] = Resolve-Page "H" "P" $true
    $resolved["O_B2_BAD"] = Resolve-Page "O" "B2" $true
    $resolved["BUS"] = Resolve-PracticePage
    return $resolved
}

try {
    $Resolved = Resolve-All

    # 两份原始权威PDF在正式测试中无法由NVDA稳定朗读。
    # 优先使用由同一PDF全文转换、未摘要改写的静态HTML。
    $AccessibleB1Sources = @{
        "R_B1" = Join-Path $Root "b1_sources\铁路旅客运输规程_无障碍离线版.html"
        "O_B1" = Join-Path $Root "b1_sources\网络购买商品七日无理由退货暂行办法_无障碍离线版.html"
    }
    foreach ($key in $AccessibleB1Sources.Keys) {
        $sourcePath = $AccessibleB1Sources[$key]
        if (-not (Test-Path -LiteralPath $sourcePath)) {
            throw "缺少NVDA可读的B1离线来源：$sourcePath。请重新解压B1无障碍启动更新包。"
        }
        $sourceFile = Get-Item -LiteralPath $sourcePath
        $Resolved[$key] = [PSCustomObject]@{
            Name = $sourceFile.Name
            FullName = $sourceFile.FullName
            SearchText = $sourceFile.Name.ToLowerInvariant()
        }
    }
} catch {
    if ($ValidateOnly) { throw }
    Clear-Host
    Write-Host "启动页自动绑定失败，未打开任何实验材料。" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host "`n请把本窗口截图发给Codex，或把 launch 文件夹的文件名列表发给Codex。"
    Read-Host "按回车退出"
    exit 1
}

# Packaging addition: resolve every binding without opening UI or collecting answers.
if ($ValidateOnly) {
    foreach ($key in ($Resolved.Keys | Sort-Object)) {
        if (-not (Test-Path -LiteralPath $Resolved[$key].FullName -PathType Leaf)) {
            throw "Missing binding: $key"
        }
        Write-Output ("{0} -> {1}" -f $key, $Resolved[$key].Name)
    }
    Write-Output ("VALIDATION_OK {0}: {1} bindings" -f $Group, $Resolved.Count)
    return
}

function Open-Page([object]$page, [string]$label) {
    Write-Host "正在打开：$label" -ForegroundColor Green
    Write-Host "文件：$($page.Name)" -ForegroundColor DarkGray
    Start-Process -FilePath $page.FullName
}

function Show-Validation {
    Clear-Host
    Write-Host "AccessWiki 启动页绑定检查" -ForegroundColor Cyan
    foreach ($key in @("R_B1","R_B2","R_P","H_B1","H_B2","H_P","O_B1","O_B2","O_P","H_P_BAD","O_B2_BAD","BUS")) {
        Write-Host ("{0,-10} -> {1}" -f $key, $Resolved[$key].Name)
    }
    Write-Host "`n只有以上12项全部对应正确，才进入正式实验。" -ForegroundColor Yellow
    Read-Host "按回车返回菜单"
}

Clear-Host
Write-Host "AccessWiki $Group 研究人员启动器" -ForegroundColor Cyan
$Participant = (Read-Host "请输入参与者编号（例如 P01）").Trim().ToUpperInvariant()
if (-not $ParticipantGroups.ContainsKey($Participant)) {
    Write-Host "参与者编号无效。请输入 P01 到 P12。" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}
if ($ParticipantGroups[$Participant] -ne $Group) {
    Write-Host "$Participant 属于 $($ParticipantGroups[$Participant])，不是 $Group。未打开材料。" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

while ($true) {
    Clear-Host
    $sequence = $Sequences[$Group]
    Write-Host "AccessWiki｜$Participant｜$Group" -ForegroundColor Cyan
    for ($i=0; $i -lt 3; $i++) {
        $topic = $sequence[$i][0]
        $condition = $sequence[$i][1]
        Write-Host "$($i+1). 第$($i+1)轮：$($TopicNames[$topic])｜$($ConditionNames[$condition])"
    }
    Write-Host "4. 探索性错误核验任务"
    Write-Host "5. 公交练习"
    Write-Host "6. 医院B1预加载"
    Write-Host "V. 查看12个启动页绑定结果"
    Write-Host "Q. 退出"
    Write-Host "`n注意：终端是研究人员界面，不要让参与者看到条件名称。" -ForegroundColor Yellow
    $choice = (Read-Host "请选择").Trim().ToUpperInvariant()

    if ($choice -in @("1","2","3")) {
        $index = [int]$choice - 1
        $topic = $sequence[$index][0]
        $condition = $sequence[$index][1]
        $key = "${topic}_${condition}"
        Open-Page $Resolved[$key] "第$choice轮｜$($TopicNames[$topic])｜$($ConditionNames[$condition])"
        Read-Host "确认页面已打开后按回车返回菜单"
    } elseif ($choice -eq "4") {
        $errorKey = $ErrorTasks[$Participant]
        $label = if ($errorKey -eq "H_P_BAD") { "医院双主播错误核验" } else { "退货单主播错误核验" }
        Open-Page $Resolved[$errorKey] $label
        Read-Host "确认页面已打开后按回车返回菜单"
    } elseif ($choice -eq "5") {
        Open-Page $Resolved["BUS"] "公交练习（不计分）"
        Read-Host "确认页面已打开后按回车返回菜单"
    } elseif ($choice -eq "6") {
        $hospitalSource = Join-Path $Root "b1_sources\outpatient_process_primary.html"
        if (-not (Test-Path $hospitalSource)) {
            Write-Host "找不到医院B1原始网页：$hospitalSource" -ForegroundColor Red
        } else {
            Start-Process -FilePath $hospitalSource
            Write-Host "已打开医院B1。请等待正文出现，确认NVDA可读，再回到页首。" -ForegroundColor Green
        }
        Read-Host "按回车返回菜单"
    } elseif ($choice -eq "V") {
        Show-Validation
    } elseif ($choice -eq "Q") {
        break
    } else {
        Write-Host "输入无效。" -ForegroundColor Red
        Start-Sleep -Seconds 1
    }
}
