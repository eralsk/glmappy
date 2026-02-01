# GLMapPy
A lightweight image editor for building block-diagram figures of regression, hierarchical models, workflows, and statistical pipelines. 

Currently catered to GLM and LM block diagrams. Further goals include allowing text to be placed anywhere on the canvas and further arrow manipulation (non-LM diagrams).
<br/>
# Version Info
This program is currently in Beta testing. Any recommendations and bug reports are greatly appreciated. 
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
Users must have Python installed to run the source code. Python is not needed for the released Windows OS executible file.

### Requirements

- Python **3.9 or newer** (tested on Python 3.11)
- Operating system: Windows, macOS, or Linux

### Python Dependencies

The following Python packages are required:

- tkinter (included with standard Python distributions)
- numpy
- matplotlib
- daft

Standard library modules (`json`, `math`, `copy`, `io`) are included with Python and require no additional installation.

### Installation

1. Clone this repository or download the source code:
   ```bash
   git clone https://github.com/yourusername/projectname.git
   cd projectname

# Citation
If you use this software or any modification of the source code in academic work, please cite:

Skogsberg, Erik (2026). GLMapPy: A Simple Way to Create LM Diagrams. GitHub repository: https://github.com/eralsk/glmappy
<br/>
## License
This project is licensed under the MIT License and is free to use, modify, and distribute. See license and third_party_notices.txt for more details.
