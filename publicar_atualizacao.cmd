@echo off
setlocal
cd /d "%~dp0"

set /p RELEASE_VERSION=Nova versao (ex.: 1.0.2): 
set /p RELEASE_NOTES=Notas da atualizacao: 

if "%RELEASE_VERSION%"=="" (
    echo A versao e obrigatoria.
    pause
    exit /b 1
)
if "%RELEASE_NOTES%"=="" (
    echo As notas da atualizacao sao obrigatorias.
    pause
    exit /b 1
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" release_update.py "%RELEASE_VERSION%" --notes "%RELEASE_NOTES%"
) else (
    python release_update.py "%RELEASE_VERSION%" --notes "%RELEASE_NOTES%"
)

if errorlevel 1 (
    echo.
    echo Publicacao interrompida. Leia a mensagem acima; nenhum manifesto foi enviado ao GitHub.
    pause
    exit /b 1
)

echo.
echo Atualizacao publicada com sucesso.
pause
