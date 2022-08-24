SET VENV=venv

py -3 -m venv %VENV%
.\%VENV%\Scripts\pip install -r .\capito\requirements.txt

setx CAPITO_BASE_DIR %CD%

@pause