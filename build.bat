rmdir build\arch14cz /S /Q
rmdir dist\arch14cz /S /Q

call ..\venv\Scripts\activate.bat

pip uninstall -y arch14cz_backend
pip cache purge
pip install .

call pyinstaller installer\arch14cz.spec

robocopy /e src\arch14cz_backend\res dist\arch14cz\arch14cz_backend\res
robocopy /e src\arch14cz_backend\data dist\arch14cz\arch14cz_backend\data
robocopy /e installer\deposit_gui_res dist\arch14cz\deposit_gui\res
robocopy /e installer\graphviz dist\arch14cz\deposit_gui\dgui\graphviz
robocopy /e installer\pygraphviz dist\arch14cz\deposit_gui\dgui\pygraphviz
copy installer\arch14cz_icon.ico dist\arch14cz
copy src\arch14cz_backend\THIRDPARTY.TXT dist\arch14cz
python installer\make_ifp.py

pip install -e .
