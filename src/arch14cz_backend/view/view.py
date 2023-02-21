from deposit_gui import (DView, DNotification)

from arch14cz_backend.view.groups.backend import Backend
from arch14cz_backend.view.groups.frontend import Frontend

from arch14cz_backend import __version__, __title__, res

from PySide2 import (QtWidgets, QtCore, QtGui)
import traceback
import os

class View(DView):
	
	APP_NAME = __title__
	VERSION = __version__
	
	def __init__(self) -> None:
		
		DView.__init__(self)
		
		self._close_callback = None
		
		self.set_res_folder(os.path.dirname(res.__file__))
		
		self.backend = Backend(self)
		self.frontend = Frontend(self)
		
		central_widget = QtWidgets.QWidget(self)
		central_widget.setStyleSheet("QWidget {font-size: 12px;}")
		central_widget.setLayout(QtWidgets.QVBoxLayout())
		self.setCentralWidget(central_widget)
		
		central_widget.layout().addWidget(self.backend)
		central_widget.layout().addWidget(self.frontend)
		central_widget.layout().addStretch()
		
		self._notification = DNotification(self)
		
		self.setWindowIcon(self.get_icon("arch14cz_icon.svg"))
	
	def set_db_name(self, name):
		
		self.backend.set_db_name(name)
	
	def set_folder(self, path, url = None):
		
		self.backend.set_folder(path, url)
	
	def set_frontend_host(self, name):
		
		self.frontend.set_host(name)
	
	def set_frontend_name(self, name):
		
		self.frontend.set_db_name(name)
	
	def set_publish_enabled(self, state):
		
		self.frontend.set_update_enabled(state)
	
	def show_notification(self, text, delay = None):
		
		self._notification.show(text, delay)
	
	def hide_notification(self):
		
		self._notification.hide()
	
	# events
	
	def exception_event(self, typ, value, tb):
		
		error_title = "%s: %s" % (str(typ), str(value)[:512])
		self.show_notification('''
Application Error: %s
(see Log File for details)
		''' % (error_title),
			delay = 7000,
		)
		text = "Exception: %s\nTraceback: %s" % (
			error_title, 
			"".join(traceback.format_tb(tb)),
		)
		self.logging.append(text)
		print(text)
	
	# overriden QMainWindow methods
	
	def closeEvent(self, event):
		
		if self._close_callback is not None:
			if not self._close_callback():
				event.ignore()
				return
		DView.closeEvent(self, event)
