Capito stands for "Computer Animation Pipeline Tools". These are scripts related to HdM Übungen CG and Stupro CA.
In the rooms 042 / 043 you have access to the latest version on drive K:\pipeline\capito (\\cg\pipeline\capito). Just use the drop-installer located there to set up capito for your HdM account (See 3.2 further down). 

# 1 Requirements
+ Maya 2022+ (capito uses the featureset of Python 3.7+)
+ PyMel

When using the Maya drop-installer (see 3.2) Capito will try to install PyMel if it is not already installed. If the automatic PyMel installation did not succed via the drop-installer please do the following:
+ Open a commandline with administrator/root privileges (*cmd* for Windows, *terminal* for Mac, *shell* for Linux)
+ Cd into the Maya install location. This is the directory where *mayapy* is located! (eg. ```cd "C:\Program Files\Autodesk\maya2022\bin"``` for Windows. You can locate this folder for other Operating Systems by typing ```import sys; print(sys.executable)``` into a Maya Python Script Editor window.)
+ Use pip with mayapy to install pymel: ```mayapy -m pip install pymel```

# 2 Download

## 2.1 Via Commandline / git bash
+ Open git bash
+ cd into the *desired location* on your computer and run:
+ ```git clone https://github.com/jobomat/capito.git```

## 2.2 Via Zip-File
Click the green "Code" Button above and download the repo as zip file. Unpack to your *desired location*

# 3 Setup

## 3.1 System Setup (Windows only)
If you only want to use the Maya portion of capito (Rig-Tools etc. for Übungen CG) you can skip this and continue with 3.2. To setup the Captio pipelining tools on Windows right-click on install_windows.bat and choose "Run as Administrator". The installation process will take several minutes depending on your internet connection. The install script will create various Python virtiual envs, set some system environment variables. You will be asked, if you would like to download FFMPEG. If you don't already have FFMPEG installed or are not familiar with setting environment variables, I recommend to say yes. Otherwise you can create an environment variable called "FFMPEG" which points to the installed ffmpeg executable (fmpeg.exe on windows).

## 3.2 Setup for Maya
Just drop the file *maya_drop_installer.py* into the *viewport* of a running Maya instance (Outliner or other editors will not work!). You will be presented with a summary of the installation process. 

If you get presented an error (Red line down to the right in Maya) it's likely that pymel wasn't installed with Maya. See (1) in this case!

If you have already created a userSetup.py the installer will ask if you want to replace it with the userSetup for capito. If a replacement is not desired it's recommended to backup your version, let the installer write it's version and merge the two files manually. If your userSetup.py was created by an old version of capito (or cg3) and you did not edit the userSetup.py you can safely replace the userSetup.py.
