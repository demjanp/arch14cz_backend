from arch14cz_backend.dialogs.dialog_connect import DialogConnect
from arch14cz_backend.dialogs.dialog_connect_frontend import DialogConnectFrontend
from arch14cz_backend.dialogs.dialog_import_excel import DialogImportExcel
from arch14cz_backend.dialogs.dialog_about import DialogAbout

from deposit_gui import DCDialogs

from PySide2 import (QtWidgets, QtCore, QtGui)
import os

class CDialogs(DCDialogs):
	
	def __init__(self, cmain, cview):
		
		DCDialogs.__init__(self, cmain, cview)
		
		self.view = cview._view
	
	# ---- Signal handling
	# ------------------------------------------------------------------------
	@QtCore.Slot()
	def on_clear_recent(self):
		
		self.view.clear_recent_connections()
	
	
	# ---- get/set
	# ------------------------------------------------------------------------
	
	
	# ---- Dialogs
	# ------------------------------------------------------------------------
	'''
	open(name, *args, **kwargs)
	
	Implement set_up_[name], process_[name] and cancel_[name] for each dialog:
	
	def set_up_[name](self, dialog, *args, **kwargs):
		
		args and kwargs are passed from DCDialogs.open(name, *args, **kwargs)
		
		dialog = QtWidgets.QDialog
		
		dialog.set_title(name)
		dialog.set_frame(frame = QtWidget)
		dialog.get_frame()
		dialog.set_button_box(ok: bool, cancel: bool): set if OK and Cancel buttons are visible
		
	def process_[name](self, dialog, *args, **kwargs):
		
		args and kwargs are passed from DCDialogs.open(name, *args, **kwargs)
		
		process dialog after OK has been clicked
	
	def cancel_[name](self, dialog, *args, **kwargs):
		
		args and kwargs are passed from DCDialogs.open(name, *args, **kwargs)
		
		handle dialog after cancel has been clicked
	'''
	
	def set_up_Connect(self, dialog, *args, **kwargs):
		
		frame = DialogConnect(dialog)
		frame.set_recent_dir(self.view.get_recent_dir())
		frame.set_recent_connections(self.view.get_recent_connections())
		frame.signal_clear_recent.connect(self.on_clear_recent)
	
	def process_Connect(self, dialog, *args, **kwargs):
		
		self.cmain.cmodel.load(**dialog.get_data())
	
	def cancel_Connect(self, dialog, *args, **kwargs):
		
		datasource = self.cmain.cmodel.get_datasource()
		if not datasource.is_valid():
			self.cmain.cmodel.load(datasource = "Memory")
	
	
	def set_up_ConnectFrontend(self, dialog):
		
		dialog.set_title("Connect Frontend Database")
		dialog.set_button_box(False, False)
		dialog.setModal(True)
		dialog.set_frame(DialogConnectFrontend(
			dialog,
			**self.cmain.cmodel.get_frontend_connection()
		))
	
	def process_ConnectFrontend(self, dialog):
		
		frame = dialog.get_frame()
		self.cmain.cmodel.set_frontend_connection(*frame.get_values())
	
	
	def set_up_ImportExcel(self, dialog):
		
		dialog.set_title("Import Excel Data")
		dialog.set_button_box(True, True)
		dialog.setModal(True)
		dialog.set_frame(DialogImportExcel(dialog, self.cmain.cview))
	
	def process_ImportExcel(self, dialog):
		
		frame = dialog.get_frame()
		path = frame.path_edit.text().strip()
		if not os.path.isfile(path):
			return
		fields = {}
		for name in frame.field_combos:
			index = frame.field_combos[name].currentIndex() - 1
			if index > -1:
				fields[name] = index
		if len(fields) < len(frame.field_names):
			return
		self.cmain.cmodel.import_excel(path, fields)
	
	
	def set_up_About(self, dialog):
		
		dialog.set_title("About Arch14CZ")
		dialog.set_button_box(True, False)
		dialog.setModal(True)
		dialog.set_frame(DialogAbout())
