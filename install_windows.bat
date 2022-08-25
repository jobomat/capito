SET VENVS=venvs
SET SYSTEM_VENV=system
SET MAYA_VENV=maya

py -3 -m venv %VENVS%\%SYSTEM_VENV%
.\%VENVS%\%SYSTEM_VENV%\Scripts\pip install -r .\capito\system_requirements.txt

py -3 -m venv %VENVS%\%MAYA_VENV%
.\%VENVS%\%MAYA_VENV%\Scripts\pip install -r .\capito\maya_requirements.txt

setx CAPITO_BASE_DIR %CD%

@pause