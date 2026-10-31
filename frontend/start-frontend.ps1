# VasoRAT 前端一键启动脚本
#
# 用途：
#   1. 检查 npm 和 node_modules
#   2. 启动 Vite 开发服务器（新开一个 PowerShell 窗口）
#   3. 等 5173 端口就绪后，用默认浏览器打开工作台
#
# 运行方式（在本目录打开 PowerShell）：
#   powershell -ExecutionPolicy Bypass -File .\start-frontend.ps1
#
# 如果执行策略限制，也可以右键本文件选择“使用 PowerShell 运行”。

$ErrorActionPreference = "Stop"

$frontendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $frontendDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " VasoRAT 前端启动器" -ForegroundColor Cyan
Write-Host " 目录：$frontendDir" -ForegroundColor DarkGray
Write-Host "========================================" -ForegroundColor Cyan

# 1. 检查运行环境
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "未找到 npm，请先安装 Node.js（建议 20 或 24）。" -ForegroundColor Red
    Write-Host "下载地址：https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "按回车退出"
    exit 1
}

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
    Write-Host "当前目录没有 package.json，请确认脚本放在 frontend 目录下。" -ForegroundColor Red
    Read-Host "按回车退出"
    exit 1
}

# 2. 首次运行自动安装依赖
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "[1/3] 首次运行，正在安装依赖（npm install）..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "依赖安装失败，请查看上方 npm 错误信息。" -ForegroundColor Red
        Read-Host "按回车退出"
        exit 1
    }
} else {
    Write-Host "[1/3] 依赖已存在，跳过 npm install。" -ForegroundColor Green
}

# 3. 判断前端是否已经在运行
function Test-Frontend {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -UseBasicParsing -TimeoutSec 1
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Test-Backend {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/projects?page=1&size=1" -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

if (-not (Test-Frontend)) {
    Write-Host "[2/3] 正在启动 Vite..." -ForegroundColor Yellow

    # 新开一个窗口运行 dev server，这样启动器窗口关闭后前端仍然继续运行
    Start-Process powershell -WorkingDirectory $frontendDir -ArgumentList @(
        "-NoProfile",
        "-NoExit",
        "-Command",
        "`$Host.UI.RawUI.WindowTitle = 'VasoRAT 前端'; npm run dev"
    )

    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Frontend) {
            $ready = $true
            break
        }
    }

    if (-not $ready) {
        Write-Host "启动超时，请查看新打开的 PowerShell 窗口中的 Vite 输出。" -ForegroundColor Red
        Read-Host "按回车退出"
        exit 1
    }
} else {
    Write-Host "[2/3] 前端已经在运行，直接打开浏览器。" -ForegroundColor Green
}

# 4. 打开默认浏览器
Write-Host "[3/3] 打开 http://127.0.0.1:5173/#/dashboard" -ForegroundColor Yellow
Start-Process "http://127.0.0.1:5173/#/dashboard"

# 前端可以单独打开，但数据来自 FastAPI，后端没启动时给出提示
if (-not (Test-Backend)) {
    Write-Host ""
    Write-Host "提示：后端 8000 端口没有响应。" -ForegroundColor Yellow
    Write-Host "      页面可以打开，但项目/模型/扰动数据会加载失败。" -ForegroundColor Yellow
    Write-Host "      请先在 PyCharm 或终端启动 FastAPI：" -ForegroundColor Yellow
    Write-Host "      cd ..\backend" -ForegroundColor DarkGray
    Write-Host "      py -3.11 -m uvicorn app.main:app --reload" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "启动完成。关闭此窗口不会影响前端服务。" -ForegroundColor Green
Start-Sleep -Seconds 3
