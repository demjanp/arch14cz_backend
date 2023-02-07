from PySide2 import (QtWidgets, QtCore, QtGui)

class DialogConnectFrontend(QtWidgets.QFrame):	
	
	def __init__(self, dialog,
			host = "",
			dbname = "",
			schema = "public",
			user = "",
			password = ""
		):
		
		QtWidgets.QFrame.__init__(self)
		
		self._dialog = dialog
		
		self.setMinimumWidth(600)
		self.setMinimumHeight(200)
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(10, 10, 10, 10)
		
		self.form = QtWidgets.QWidget()
		self.form.setLayout(QtWidgets.QFormLayout())
		
		self.host_edit = QtWidgets.QLineEdit(host)
		self.host_edit.textChanged.connect(self.update)
		
		self.dbname_edit = QtWidgets.QLineEdit(dbname)
		self.dbname_edit.textChanged.connect(self.update)
		
		self.schema_edit = QtWidgets.QLineEdit(schema)
		self.schema_edit.textChanged.connect(self.update)
		
		self.user_edit = QtWidgets.QLineEdit(user)
		self.user_edit.textChanged.connect(self.update)
		
		self.pass_edit = QtWidgets.QLineEdit(password)
		self.pass_edit.setEchoMode(QtWidgets.QLineEdit.Password)
		self.pass_edit.textChanged.connect(self.update)
		
		self.connect_button = QtWidgets.QPushButton("Connect")
		self.connect_button.setEnabled(False)
		self.connect_button.clicked.connect(self.on_connect)
		
		self.form.layout().addRow("Host[:port]:", self.host_edit)
		self.form.layout().addRow("Database:", self.dbname_edit)
		self.form.layout().addRow("Schema:", self.schema_edit)
		self.form.layout().addRow("Username:", self.user_edit)
		self.form.layout().addRow("Password:", self.pass_edit)
		
		button_container = QtWidgets.QWidget()
		button_container.setLayout(QtWidgets.QHBoxLayout())
		button_container.layout().setContentsMargins(0, 0, 0, 0)
		button_container.layout().addStretch()
		button_container.layout().addWidget(self.connect_button)
		button_container.layout().addStretch()
		
		self.layout().addWidget(self.form)
		self.layout().addWidget(button_container)
		self.layout().addStretch()
		
		self.update()
	
	def get_values(self):
		
		host = self.host_edit.text().strip()
		dbname = self.dbname_edit.text().strip()
		schema = self.schema_edit.text().strip()
		user = self.user_edit.text().strip()
		password = self.pass_edit.text().strip()
		if host and (":" not in host):
			host = "%s:5432" % (host)
		
		return host, dbname, schema, user, password
	
	@QtCore.Slot()
	def update(self):
		
		self.connect_button.setEnabled(
			("" not in list(self.get_values()))
		)
	
	@QtCore.Slot()
	def on_connect(self):
		
		self._dialog.accept()
