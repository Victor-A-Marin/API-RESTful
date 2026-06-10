@echo off
title Iniciando API Hexagonal

set PYTHON_CMD=python

if exist ".venv\Scripts\python.exe" (
    echo [+] Ambiente virtual encontrado: .venv
    set PYTHON_CMD=.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    echo [+] Ambiente virtual encontrado: venv
    set PYTHON_CMD=venv\Scripts\python.exe
) else if exist "env\Scripts\python.exe" (
    echo [+] Ambiente virtual encontrado: env
    set PYTHON_CMD=env\Scripts\python.exe
) else (
    echo [!] Nenhum ambiente virtual encontrado. Usando Python global.
)

echo [*] Ligando o servidor backend...
start cmd /k "%PYTHON_CMD% main.py"

timeout /t 2 /nobreak >nul

echo [+] Abrindo o Swagger no Chrome...
start chrome "http://127.0.0.1:8000/docs"

exit