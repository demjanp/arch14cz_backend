# Arch14CZ - Backend
Backend interface for Arch14CZ - the database of archaeological radiocarbon dates of the Czech Republic

Created on 5. 2. 2023

<details>
<summary>Table of Contents</summary>

1. [About Arch14CZ](#about)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Developer Notes](#developer)
5. [Contact](#contact)
6. [Acknowledgements](#acknowledgements)
7. [License](#license)

</details>

## About Arch14CZ - Backend <a name="about"></a>
Backend graphical user interface for Arch14CZ - the database of archaeological radiocarbon dates of the Czech Republic.

For the frontend interface see the [arch14cz_frontend](https://github.com/demjanp/arch14cz_frontend) project.

### Database Schema
`TODO`

## Installation <a name="installation"></a>

For a Windows installer see:

[https://github.com/demjanp/arch14cz_backend/releases/latest](https://github.com/demjanp/arch14cz_backend/releases/latest)

## Usage <a name="usage"></a>
### Connecting to a Backend Database
`TODO`

### Data Entry
`TODO`

### Importing Excel Data
`TODO`

### Choosing a Radiocarbon Calibration Curve
`TODO`

### Publishing Data
`TODO`

## Developer Notes <a name="developer"></a>
### Preparing the Virtual Environment

Arch14CZ - Backend requires Python 3 and a Windows environment. To prepare a Python virtual environment for development:

1. Open a terminal or command prompt window.
2. Navigate to the Arch14CZ - Backend root directory: 
<pre><code>cd [path to local Arch14CZ - Backend dir]</code></pre>
3. Create the virtual environment:
<pre><code>python -m venv [VE dir name e.g. 'venv']</code></pre>
4. Activate the virtual environment:
<pre><code>venv\Scripts\activate.bat</code></pre>
5. To exit the virtual environment:
<pre><code>deactivate</code></pre>

### Cloning the GitHub Project

To clone the `arch14cz_backend` GitHub project, follow these steps:

1. Make sure you have [Git](https://git-scm.com/downloads) installed on your computer.
2. Open a terminal or command prompt window.
3. Navigate to the Arch14CZ - Backend root directory.
4. Run the following command:
<pre><code>git clone https://github.com/demjanp/arch14cz_backend.git</code></pre>
5. The repository will be cloned to a new directory named `arch14cz_backend` in your current directory.
6. Change into the newly created directory:
<pre><code>cd arch14cz_backend</code></pre>
7. To install dependencies run the following command:
<pre><code>pip install -e .</code></pre>
8. To start the GUI run the following commands:
<pre><code>cd bin
python start_arch14cz.py</code></pre>

### Building a Windows Executable
1. Make sure you have [InstallForge](https://installforge.net/download/) installed on your computer.
2. Update absolute paths in `installer\arch14cz_installer.tpl` in the following sections:
<pre><code>[Graphics]
	Wizard image
	Header image
[Build]
	File
	SetupIconPath
	UninstallIconPath</code></pre>
3. Update virtual environment path in `installer\arch14cz.spec` in the part `pathex=['..\\venv\\Lib\\site-packages'],`.
5. Activate the virtual environment.
6. Execute the following commands once per virtual environment:
<pre><code>python -m pip install --upgrade build
pip install pyinstaller</code></pre>
6. Deactivate the virtual environment.
7. Run `build.bat`.
8. Run InstallForge and open the file `installer\arch14cz_installer.ifp`.
9. Using the Build command in InstallForge to build the installer.

## Contact: <a name="contact"></a>
Peter Demján (peter.demjan@gmail.com)

Institute of Archaeology of the Czech Academy of Sciences, Prague, v.v.i.

## Acknowledgements <a name="acknowledgements"></a>

Development of this software was supported by OP RDE, MEYS, under the project "Ultra-trace isotope research in social and environmental studies using accelerator mass spectrometry", Reg. No. CZ.02.1.01/0.0/0.0/16_019/0000728.

This software uses the following open source packages:
* [Deposit](https://github.com/demjanp/deposit)
* [Deposit GUI](https://github.com/demjanp/deposit_gui)
* [NetworkX](https://networkx.org/)
* [NumPy](https://www.numpy.org/)
* [openpyxl](https://openpyxl.readthedocs.io/)
* [Psycopg](https://psycopg.org/)
* [PySide2](https://www.pyside.org/)
* [Qt](https://www.qt.io)
* [SciPy](https://scipy.org/)

## License <a name="license"></a>

This code is licensed under the [GNU GENERAL PUBLIC LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) - see the [LICENSE](LICENSE) file for details
