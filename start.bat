@echo off
title Litematica to Schematic Converter
color 0a

echo ===================================================
echo Litematica to Schematic Converter
echo ===================================================
echo.

:: Prompt user for the filename
set /p dosya_adi="Enter the filename to convert (e.g. house.litematic): "

echo.
echo Processing, please wait...
echo.

:: Run Python converter script with user input
python convert.py "%dosya_adi%"

echo.
pause