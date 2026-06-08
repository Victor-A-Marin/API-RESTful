@echo off
title Iniciando API Hexagonal

echo [*] Ligando o servidor backend...
:: Removemos o /min porque agora você PRECISA ver o terminal para digitar o Webhook
start cmd /k "python main.py"

timeout /t 2 /nobreak >nul

echo [+] Abrindo o Swagger no Chrome...
start chrome "http://127.0.0.1:8000/docs"

exit