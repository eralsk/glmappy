# GLMapPy
A simple Python runtime that makes the process of creating publication-quality statistical model diagrams simple. 

Currently catered to GLM and LM block diagrams. Further goals include allowing text to be placed anywhere on the canvas and further arrow manipulation.
<br/>
# Version Info
This program is currently in Beta testing. Any recommendations and bug reports are greatly appreciated. 
Developed for Windows OS.
-------------------------------
Version: BETA 1.0

Changes:
- Mouse support for coordinate input for objects.
- Added a fixed preview window for export purposes.
- GLMapPy projects are now saved and loaded via .json files.
- Zoom in and Zoom out function so that canvas size is not an issue in program viewer.
- Ability to export raw Python code for the diagram.
- Optimization: the program now preloads canvas renders in memory. This fixes the issue where the canvas would "flash" when adding a new object or refreshing.
- Optimization: ruler view has been temporarily removed as it interferes with grid lines when adding nodes.

## Installation
Since the .exe was created with PyInstaller, the installation process is as easy as downloading the .exe and running it. That's it. 
## Citation
If you use this software in academic work, please cite:

Skogsberg, Erik (2026). GLMapPy: A Simple Way to Create LM Diagrams. GitHub repository: https://github.com/eralsk/glmappy
<br/>
## License
This project is licensed under the MIT License and is free to use, modify, and distribute. See license and third_party_notices.txt for more details.
