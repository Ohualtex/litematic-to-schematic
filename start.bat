@echo off
setlocal
title Litematica to Schematic Converter
color 0a

echo ===================================================
echo Litematica to Schematic Converter
echo ===================================================
echo.

set "input_file=%~1"

if "%input_file%"=="" (
    set /p input_file="Enter the filename to convert (or drag and drop here): "
)

:: Strip surrounding double quotes if present
if defined input_file (
    set "input_file=%input_file:"=%"
)

if "%input_file%"=="" (
    echo Error: No file provided.
    echo.
    pause
    exit /b 1
)

echo.
echo Processing, please wait...
echo.

:: Run Python converter script with sanitized input
python convert.py "%input_file%"

echo.
pause
