Capito stands for "Computer Animation Pipeline Tools". These are scripts related to HdM Übungen CG and Stupro CA.
In the rooms 042 / 043 you have access to the latest version on drive K:\pipeline\capito (\\cg\pipeline\capito). Just use the drop-installer located there to set up capito for your HdM account (See 3.1 further down). 

# 1 Requirements
+ Maya 2022+ (capito uses the featureset of Python 3.7.7)
+ PyMel

If you did not install PyMel with Maya 2022+ please do the following:
+ Open a commandline with administrator/root privileges (*cmd* for Windows, *terminal* for Mac, *shell* for Linux)
+ Cd into the Maya install location (eg. ```cd "C:\Program Files\Autodesk\maya2022\bin"``` for Windows). It has to be the directory where *mayapy* is located!
+ Use pip with mayapy to install pymel: ```mayapy -m pip install pymel```

# 2 Download

## 2.1 Via Commandline / git bash
+ Open git bash
+ cd into the *desired location* on your computer and run:
+ ```git clone https://github.com/jobomat/capito.git```

## 2.2 Via Zip-File
Click the green "Code" Button above and download the repo as zip file. Unpack to your *desired location*

# 3 Setup

## 3.1 Setup for Maya
Just drop the file *maya_drop_installer.py* into the *viewport* of a running Maya instance (Outliner or other editors will not work!). You will be presented with a summary of the installation process. If you have already created a userSetup.py the installer will ask if you want to replace it with the userSetup for capito. If a replacement is not desired it's recommended to backup your version, let the installer write it's version and merge the two files manually. If your userSetup.py was created by an old version of capito (or cg3) and you did not edit the userSetup.py you can safely replace the userSetup.py.
