from deposit_gui.dgui.dconnect_frame import DConnectFrame
from deposit_gui.dgui.dclickable_logo import DClickableLogo

import arch14cz_backend

from PySide2 import (QtWidgets, QtCore, QtGui)
import os

class DialogConnect(DConnectFrame):
	
	def __init__(self, dialog):
		
		DConnectFrame.__init__(self, dialog)
	
	def title(self):
		
		return "Select Data Source"
	
	def creating_enabled(self):
		
		return True
	
	def logo(self):
		
		path = os.path.join(os.path.dirname(arch14cz_backend.__file__), "res/arch14cz_logo.svg")
		
		logo_frame = QtWidgets.QFrame()
		logo_frame.setLayout(QtWidgets.QVBoxLayout())
		logo_frame.layout().setContentsMargins(0, 0, 0, 0)
		logo_frame.layout().addStretch()
		logo_frame.layout().addWidget(
			DClickableLogo(
				path,
				"https://github.com/demjanp/arch14cz_backend",
				alignment = QtCore.Qt.AlignCenter,
			)
		)
		logo_frame.layout().addStretch()
		
		return logo_frame
