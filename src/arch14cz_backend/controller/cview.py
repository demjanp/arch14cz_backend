from deposit_gui import AbstractSubcontroller

from arch14cz_backend.view.view import View

from PySide2 import (QtWidgets, QtCore, QtGui)
from pathlib import Path
import json
import os

class CView(AbstractSubcontroller):
	
	def __init__(self, cmain) -> None:
		
		AbstractSubcontroller.__init__(self, cmain)
		
		self._view = View()
		
		self._view.backend.signal_folder_link_clicked.connect(
			self.on_folder_link_clicked
		)
		self._view.backend.signal_connect_clicked.connect(
			self.on_connect_clicked
		)
		self._view.backend.signal_open_clicked.connect(
			self.on_open_clicked
		)
		self._view.backend.signal_import_clicked.connect(
			self.on_import_clicked
		)
		
		self._view.frontend.signal_connect_clicked.connect(
			self.on_frontend_connect_clicked
		)
		self._view.frontend.signal_update_clicked.connect(
			self.on_frontend_update_clicked
		)
		
		self.progress = self._view.progress
		
		self._view._close_callback = self.cmain.on_close
	
	def show(self):
		
		self._view.show()
	
	
	# ---- Signal handling
	# ------------------------------------------------------------------------
	@QtCore.Slot()
	def on_connect_clicked(self):
		
		self.cmain.cdialogs.open("Connect")
		
	@QtCore.Slot()
	def on_open_clicked(self):
		
		self.cmain.open_deposit()
	
	@QtCore.Slot()
	def on_import_clicked(self):
	
		self.cmain.cdialogs.open("ImportExcel")
	
	@QtCore.Slot(str)
	def on_folder_link_clicked(self, path):
		
		self.cmain.open_folder(path)
	
	@QtCore.Slot()
	def on_frontend_connect_clicked(self):
		
		self.cmain.cdialogs.open("ConnectFrontend")
	
	@QtCore.Slot()
	def on_frontend_update_clicked(self):
		
		if self.show_question(
			"Publish Database",
			"Are you sure to publish current database?"
		):
			self.cmain.cmodel.update_frontend()
	
	
	# ---- get/set
	# ------------------------------------------------------------------------
	def get_default_folder(self):
		
		folder = self._view.get_recent_dir()
		if folder:
			return folder
		
		if self.cmain.cmodel.has_local_folder():
			return self.cmain.cmodel.get_folder()
		
		return str(Path.home())
	
	def get_save_path(self, caption, filter, filename = None):
		# returns path, format
		
		folder = self.get_default_folder()
		if filename is not None:
			folder = os.path.join(folder, filename)
		path, format = QtWidgets.QFileDialog.getSaveFileName(self._view, dir = folder, caption = caption, filter = filter)
		
		return path, format
	
	def get_load_path(self, caption, filter, dir = None):
		
		if dir is None:
			dir = self.get_recent_dir()
		path, format = QtWidgets.QFileDialog.getOpenFileName(self._view, dir = dir, caption = caption, filter = filter)
		
		return path, format
	
	def get_logging_path(self):
		
		return self._view.logging.get_log_path()
	
	def get_existing_folder(self, caption):
		
		folder = QtWidgets.QFileDialog.getExistingDirectory(self._view, dir = self.get_default_folder(), caption = caption)
		
		return folder
	
	def get_recent_dir(self):
		
		return self._view.get_recent_dir()
	
	def set_registry(self, name, data):
		
		self._view.registry.set(name, json.dumps(data))
	
	def get_registry(self, name, default = None):
		
		data = self._view.registry.get(name)
		if not data:
			return default
		return json.loads(data)
	
	def set_title(self, title):
		
		self._view.set_title(title)
	
	def set_db_name(self, name):
		
		self._view.set_db_name(name)
	
	def set_folder(self, path, url = None):
		
		self._view.set_folder(path, url)
	
	def set_frontend_host(self, name):
		
		self._view.set_frontend_host(name)
	
	def set_frontend_name(self, name):
		
		self._view.set_frontend_name(name)
	
	def set_publish_enabled(self, state):
		
		self._view.set_publish_enabled(state)
	
	def set_recent_dir(self, path):
		
		if os.path.isfile(path):
			path = os.path.dirname(path)
		if not os.path.isdir(path):
			return
		self._view.set_recent_dir(path)
	
	def set_status_message(self, text):
		
		self._view.statusbar.message(text)
	
	def log_message(self, text):
		
		self._view.logging.append(text)
	
	def show_notification(self, text, delay = None):
		
		self._view.show_notification(text, delay)
	
	def hide_notification(self):
		
		self._view.hide_notification()
	
	def show_information(self, caption, text):
		
		QtWidgets.QMessageBox.information(self._view, caption, text)
	
	def show_warning(self, caption, text):
		
		QtWidgets.QMessageBox.warning(self._view, caption, text)
	
	def show_question(self, caption, text):
		
		reply = QtWidgets.QMessageBox.question(self._view, caption, text)
		
		return reply == QtWidgets.QMessageBox.Yes
	
	def show_input_dialog(self, caption, text, value = "", **kwargs):
		
		return self._view.show_input_dialog(caption, text, value, **kwargs)
	
	def close(self):
		
		self._view.close()

