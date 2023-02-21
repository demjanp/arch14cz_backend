
from PySide2 import (QtWidgets, QtCore, QtGui)

class Frontend(QtWidgets.QGroupBox):
	
	signal_connect_clicked = QtCore.Signal()
	signal_update_clicked = QtCore.Signal()
	
	def __init__(self, view):
		
		QtWidgets.QGroupBox.__init__(self, "Frontend Database")
		
		self.setStyleSheet("QGroupBox {font-weight: bold;}")
		self.setLayout(QtWidgets.QVBoxLayout())
		
		self._host_label = QtWidgets.QLabel("Host: ")
		self._dbname_label = QtWidgets.QLabel("Database: ")
		
		self.button_connect = QtWidgets.QPushButton(
			view.get_icon("connect.svg"), "Connect"
		)
		self.button_connect.clicked.connect(self.on_connect)
		
		self.button_update = QtWidgets.QPushButton(
			view.get_icon("publish.svg"), "Publish"
		)
		self.button_update.clicked.connect(self.on_update)
		
		button_box = QtWidgets.QFrame()
		button_box.setLayout(QtWidgets.QHBoxLayout())
		button_box.layout().setContentsMargins(0, 0, 0, 0)
		button_box.layout().addWidget(self.button_connect)
		button_box.layout().addWidget(self.button_update)
		button_box.layout().addStretch()
		
		self.layout().addWidget(self._host_label)
		self.layout().addWidget(self._dbname_label)
		self.layout().addWidget(button_box)
	
	@QtCore.Slot()
	def on_connect(self):
		
		self.signal_connect_clicked.emit()
	
	@QtCore.Slot()
	def on_update(self):
		
		self.signal_update_clicked.emit()
	
	def set_host(self, name):
		
		self._host_label.setText("Host: <b>%s</b>" % (name))
	
	def set_db_name(self, name):
		
		self._dbname_label.setText("Database: <b>%s</b>" % (name))
	
	def set_update_enabled(self, state):
		
		self.button_update.setEnabled(state)


