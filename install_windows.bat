pushd "%~dp0"
@ECHO off
SET VENVS=venvs
SET SYSTEM_VENV=system
SET MAYA_VENV=maya
SET FFMPEG_DIR=ffmpeg-master-latest-win64-gpl

REM Install the virtual environments for different apps
py -3 -m venv %VENVS%\%SYSTEM_VENV%
.\%VENVS%\%SYSTEM_VENV%\Scripts\pip install -r .\capito\system_requirements.txt

py -3 -m venv %VENVS%\%MAYA_VENV%
.\%VENVS%\%MAYA_VENV%\Scripts\pip install -r .\capito\maya_requirements.txt

REM Set the CAPITO_BASE_DIR environment variable to current directory.
setx CAPITO_BASE_DIR %CD%

%SystemRoot%\System32\choice.exe /C YN /N /M "Download FFMPEG now? [Y/N]"
if not errorlevel 1 goto DOWNLOAD
if errorlevel 2 goto SKIP

:DOWNLOAD
REM Execute the python script to download 3rd party programs (ffmpeg)
.\%VENVS%\%SYSTEM_VENV%\Scripts\python .\capito\get_vendor_apps.py
REM Clean up downloaded packed files
del vendor\ffmpeg
REM set FFMPEG environment variable to ffmpeg.exe
setx FFMPEG "%CD%\vendor\%FFMPEG_DIR%\bin\ffmpeg.exe"
REM add ffmpeg dir to users PATH (Not really necessary but convenient for plumbum import)
for /f "usebackq tokens=2,*" %%A in (`reg query HKCU\Environment /v PATH`) do set my_user_path=%%B
setx PATH "%CD%\vendor\%FFMPEG_DIR%\bin\;%my_user_path%"
:SKIP
echo ---------------------
echo Installation beendet.
echo ---------------------
@pause

popd
