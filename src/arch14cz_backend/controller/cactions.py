from deposit_gui import DCActions

import os

class CActions(DCActions):
	
	def __init__(self, cmain, cview) -> None:
		
		DCActions.__init__(self, cmain, cview)
		
		self.update()
	
	# ---- Signal handling
	# ------------------------------------------------------------------------
	
	
	# ---- get/set
	# ------------------------------------------------------------------------
	
	
	# ---- Actions
	# ------------------------------------------------------------------------
	def set_up_tool_bar(self):
		
		return {
			"Backend": [
				("Connect", "Connect"),
				("Save", "Save"),
				("Deposit", "Open"),
				None,
				("ImportExcel", "Import Excel Data"),
			],
			"Frontend": [
				("Publish", "Publish Frontend Database"),
			],
		}
	
	def set_up_menu_bar(self):
		
		return {
			"Backend": [
				("Connect", "Connect"),
				("Save", "Save"),
				("Deposit", "Open"),
				None,
				("AutoBackup", "Backup backend after every save"),
				("CreateSchema", "Create Schema"),
				("ImportExcel", "Import Excel Data"),
			],
			"Frontend": [
				("ConnectFrontend", "Connect"),
				("Publish", "Publish Frontend Database"),
			],
			"Settings": [
				("CalCurve", "Calibration Curve"),
			],
			"Help": [
				("About", "About"),
				("LogFile", "Log File"),
			],
		}
	
	
	# implement update_[name] and on_[name] for each action
	'''
	def update_[name](self):
		
		return dict(
			caption = "Caption",
			icon = "icon.svg",
			shortcut = "Ctrl+S",
			help = "Tool tip",
			combo: list,
			checkable = True,
			checked = True,
			enabled = True,
		)
	
	def on_[name](self, state):
		
		pass
	'''
	
	def update_Connect(self):
		
		return dict(
			icon = "connect.svg",
			help = "Connect to Backend Database",
			checkable = False,
			enabled = True,
		)
	
	def on_Connect(self, state):
		
		self.cmain.cdialogs.open("Connect")
	
	
	def update_Save(self):
		
		return dict(
			icon = "save.svg",
			help = "Save",
			checkable = False,
			enabled = not self.cmain.cmodel.is_saved(),
		)
	
	def on_Save(self, state):
		
		if self.cmain.cmodel.can_save():
			self.cmain.cmodel.save()
		else:
			self.on_SaveAsFile(True)
	
	def update_Deposit(self):
		
		return dict(
			icon = "browser.svg",
			help = "Open Backend Database",
			checkable = False,
			enabled = True,
		)
	
	def on_Deposit(self, state):
		
		self.cmain.open_deposit()
	
	
	def update_ImportExcel(self):
		
		return dict(
			icon = "import_xls.svg",
			help = "Import Excel Data",
			checkable = False,
			enabled = True,
		)
	
	def on_ImportExcel(self, state):
		
		self.cmain.cview.on_import_clicked()
	
	
	def update_ConnectFrontend(self):
		
		return dict(
			icon = "connect.svg",
			help = "Connect to Frontend Database",
			checkable = False,
			enabled = True,
		)
	
	def on_ConnectFrontend(self, state):
		
		self.cmain.cdialogs.open("ConnectFrontend")
	
	
	def update_Publish(self):
		
		return dict(
			icon = "publish.svg",
			help = "Publish Frontend Database",
			checkable = False,
			enabled = self.cmain.cmodel.has_frontend(),
		)
	
	def on_Publish(self, state):
		
		self.cmain.cview.on_frontend_update_clicked()
	
	
	def update_AutoBackup(self):
		
		return dict(
			help = "Backup backend database after every save",
			checkable = True,
			checked = self.cmain.cmodel.has_auto_backup(),
			enabled = True,
		)
	
	def on_AutoBackup(self, state):
		
		self.cmain.cmodel.set_auto_backup(state)
	
	
	def update_CreateSchema(self):
		
		return dict(
			help = "Create Arch14CZ Schema in the Database",
			checkable = False,
			enabled = True,
		)
	
	def on_CreateSchema(self, state):
		
		if self.cmain.cview.show_question(
			"Create Schema",
			"Create the Arch14CZ schema in the database?"
		):
			self.cmain.cmodel.create_schema()
	
	
	def update_CalCurve(self):
		
		return dict(
			help = "Select Calibration Curve",
			checkable = False,
			enabled = True,
		)
	
	def on_CalCurve(self, state):
		
		dir = os.path.dirname(self.cmain.cmodel.get_cal_curve())
		path, format = self.cmain.cview.get_load_path(
			"Select Calibration Curve File",
			"Calibration Curve (*.14c)",
			dir = dir
		)
		if path is None:
			return
		self.cmain.cview.set_recent_dir(path)
		self.cmain.cmodel.set_cal_curve(path)
	
	
	def on_About(self, state):
		
		self.cmain.cdialogs.open("About")
	
	
	def on_LogFile(self, state):
		
		self.cmain.open_in_external(self.cmain.cview.get_logging_path())

