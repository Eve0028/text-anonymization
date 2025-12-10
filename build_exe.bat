@echo off
REM Download Stanza models into stanza_models/ (required before bundling)
python download_models.py

REM Build single-file Windows executable including the models dir
REM The --add-data parameter on Windows uses semicolon to separate src and dest
pyinstaller --onefile --windowed --add-data "stanza_models;stanza_models" main.py

echo Build finished. Check the dist\\main.exe
