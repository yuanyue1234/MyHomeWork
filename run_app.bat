@echo off
echo 正在启动 app.py...

:: 检查 app.py 是否存在
if not exist "app.py" (
    echo 错误：找不到 app.py 文件
    pause
    exit /b 1
)

:: 尝试运行 app.py
python app.py

:: 检查是否成功运行
if %errorlevel% neq 0 (
    echo 运行 app.py 时发生错误
    pause
    exit /b 1
)

echo app.py 已成功运行
pause