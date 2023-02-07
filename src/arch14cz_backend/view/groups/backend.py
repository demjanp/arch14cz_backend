
from deposit.utils.fnc_files import (as_url, url_to_path)

from PySide2 import (QtWidgets, QtCore, QtGui)

class Backend(QtWidgets.QGroupBox):
	
	signal_folder_link_clicked = QtCore.Signal(str)		# path
	signal_connect_clicked = QtCore.Signal()
	signal_open_clicked = QtCore.Signal()
	signal_import_clicked = QtCore.Signal()
	
	def __init__(self, view):
		
		QtWidgets.QGroupBox.__init__(self, "Backend Database")
		
		self.setStyleSheet("QGroupBox {font-weight: bold;}")
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self._dbname_label = QtWidgets.QLabel("Database: ")
		self._folder_label = QtWidgets.QLabel("Local Folder: ")
		self._folder_label.setWordWrap(True)
		self._folder_label.linkActivated.connect(self.on_folder_link)
		
		button_connect = QtWidgets.QPushButton(
			view.get_icon("connect.svg"), "Connect"
		)
		button_connect.clicked.connect(self.on_connect)
		
		button_open = QtWidgets.QPushButton(
			view.get_icon("browser.svg"), "Open"
		)
		button_open.clicked.connect(self.on_open)
		
		button_import = QtWidgets.QPushButton(
			view.get_icon("import_xls.svg"), "Import"
		)
		button_import.clicked.connect(self.on_import)
		
		button_box = QtWidgets.QFrame()
		button_box.setLayout(QtWidgets.QHBoxLayout())
		button_box.layout().setContentsMargins(0, 0, 0, 0)
		button_box.layout().addWidget(button_connect)
		button_box.layout().addWidget(button_open)
		button_box.layout().addWidget(button_import)
		button_box.layout().addStretch()
		
		self.layout().addWidget(self._dbname_label)
		self.layout().addWidget(self._folder_label)
		self.layout().addWidget(button_box)
	
	@QtCore.Slot()
	def on_connect(self):
		
		self.signal_connect_clicked.emit()
	
	@QtCore.Slot()
	def on_open(self):
		
		self.signal_open_clicked.emit()
	
	@QtCore.Slot()
	def on_import(self):
		
		self.signal_import_clicked.emit()
	
	@QtCore.Slot(str)
	def on_folder_link(self, url):
		
		self.signal_folder_link_clicked.emit(url_to_path(url))
	
	def set_db_name(self, name):
		
		self._dbname_label.setText("Database: <b>%s</b>" % (name))
	
	def set_folder(self, path, url = None, max_path_length = 10):
		
		if path:
			if url is None:
				url = as_url(path)
			if len(path) > max_path_length:
				path = "\\ ".join(path.split("\\"))
			self._folder_label.setText("Local Folder: <a href=\"%s\">%s</a>" % (url, path))
		else:
			self._folder_label.setText("Local Folder: <b>not set</b>")
