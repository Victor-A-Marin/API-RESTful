@echo off
title Iniciando API Hexagonal

:: 1. Inicia o servidor Uvicorn em uma nova janela oculta/minimizada
echo [*] Ligando o servidor backend...
start /min cmd /k "python main.py"

:: 2. Aguarda 2 segundos para garantir que o Uvicorn subiu antes de abrir o navegador
timeout /t 2 /nobreak >nul

:: 3. Abre o Chrome direto no Swagger
echo [+] Abrindo o Swagger no Chrome...
start chrome "http://127.0.0.1:8000/docs"

:: 4. Fecha esta janela inicial de comandos
exit