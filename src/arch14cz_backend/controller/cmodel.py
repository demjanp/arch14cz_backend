from deposit_gui.dgui.dcmodel import DCModel

from deposit.datasource import (AbstractDatasource, Memory)
from deposit.utils.fnc_files import (as_url)
from deposit.utils.fnc_serialize import (encrypt_password)

from arch14cz_backend.utils.fnc_frontend import (check_connection, publish_data)
from arch14cz_backend.utils.fnc_import import (create_schema, generate_ids, import_xlsx)
from arch14cz_backend.utils.fnc_phasing import (update_datings, update_order, vis_order)
from arch14cz_backend.utils.fnc_radiocarbon import (update_ranges)

import arch14cz_backend

import os

class CModel(DCModel):
	
	def __init__(self, cmain):
		
		DCModel.__init__(self, cmain)
		
		self._frontend_connection = {}
		self._frontend_valid = False
		self._cal_curve = os.path.join(os.path.dirname(arch14cz_backend.__file__), "data", "intcal20.14c")
		
	
	# ---- Signal handling
	# ------------------------------------------------------------------------
	def on_added(self, objects, classes):
		# elements = [DObject, DClass, ...]
		
		self.cmain.cactions.update()
	
	def on_deleted(self, objects, classes):
		# elements = [obj_id, name, ...]
		
		self.cmain.cactions.update()
	
	def on_changed(self, objects, classes):
		# elements = [DObject, DClass, ...]
		
		self.cmain.cactions.update()
	
	def on_saved(self, datasource):
		
		self.cmain.cview.set_status_message("Saved: %s" % (str(datasource)))
		self.cmain.cactions.update()
		
	def on_loaded(self):
		
		self.update_model_info()
		self.cmain.cactions.update()
	
	
	# ---- get/set
	# ------------------------------------------------------------------------
	def has_frontend(self):
		
		return self._frontend_valid
	
	def get_frontend_host(self):
		
		if not self.has_frontend():
			return ""
		return self._frontend_connection.get("host", "")
	
	def get_frontend_name(self):
		
		if not self.has_frontend():
			return ""
		return self._frontend_connection.get("dbname", "")
	
	def get_frontend_connection(self):
		
		data = dict(
			host = "",
			dbname = "",
			schema = "public",
			user = "",
			password = ""
		)
		data.update(self._frontend_connection)
		
		return data
	
	def set_frontend_connection(self,
			host = "",
			dbname = "",
			schema = "public",
			user = "",
			password = ""
		):
		
		self._frontend_connection = dict(
			host = host,
			dbname = dbname,
			schema = schema,
			user = user,
			password = password,
		)
		
		ret = check_connection(**self._frontend_connection)
		if ret == True:
			self._frontend_valid = True
		else:
			self._frontend_valid = False
			self.cmain.cview.show_notification(ret)
		
		self.update_model_info()
		self.cmain.cactions.update()
		
		data = self._frontend_connection.copy()
		if password:
			data["password"] = encrypt_password(password)
		self.cmain.cview.set_registry("frontend_connection", data)
	
	def update_frontend(self):
		
		path_curve = self.get_cal_curve()
		path_log = as_url(self.cmain.cview.get_logging_path())
		frontend_connection = self.get_frontend_connection()
		
		self.cmain.cview.progress.show("Publishing")
		n_published, n_rows, errors = publish_data(self, frontend_connection, path_curve, self.cmain.cview.progress)
		self.cmain.cview.progress.stop()
		self.cmain.cview.show_notification(
			'''Published %d/%d rows with %d errors.<br>(see <a href="%s">Log File</a> for details)''' % (
				n_published, n_rows, len(errors), path_log
			), delay = 7000
		)
		self.cmain.cview.log_message(
			"Published %d/%d rows.\nError Messages:\n%s" % (
				n_published, n_rows, "\n".join(errors)
			)
		)
	
	def create_schema(self):
		
		self.cmain.cview.progress.show("Creating Schema")
		self._model.blockSignals(True)
		create_schema(self)
		self.cmain.cview.progress.stop()
		self._model.blockSignals(False)
		self.on_changed([],[])
		
	
	def update_datings(self):
		
		update_datings(self)
	
	def calc_order(self):
		
		self.cmain.cview.progress.show("Calculating")
		self._model.blockSignals(True)
		path_log = as_url(self.cmain.cview.get_logging_path())
		errors = update_order(self, progress = self.cmain.cview.progress)
		self.cmain.cview.progress.stop()
		self.cmain.cview.show_notification(
			'''Updated order of relative dates with %d errors.<br>(see <a href="%s">Log File</a> for details)''' % (
				len(errors), path_log
			)
		)
		self.cmain.cview.log_message(
			"Updated order of relative dates.\nError Messages:\n%s" % (
				"\n".join(errors)
			)
		)
		self._model.blockSignals(False)
		self.on_changed([],[])
	
	def calc_ranges(self):
		
		self.cmain.cview.progress.show("Calibrating")
		self._model.blockSignals(True)
		path_curve = self.get_cal_curve()
		path_log = as_url(self.cmain.cview.get_logging_path())
		errors, cnt = update_ranges(self, path_curve, progress = self.cmain.cview.progress)
		self.cmain.cview.progress.stop()
		self.cmain.cview.show_notification(
			'''Calibrated %d C-14 dates with %d errors.<br>(see <a href="%s">Log File</a> for details)''' % (
				cnt - 1, len(errors), path_log
			)
		)
		self.cmain.cview.log_message(
			"Calibrated %d C-14 dates.\nError Messages:\n%s" % (
				cnt - 1, "\n".join(errors)
			)
		)
		self._model.blockSignals(False)
		self.on_changed([],[])
	
	def update_ids(self):
		
		self.cmain.cview.progress.show("Generating")
		self._model.blockSignals(True)
		path_log = as_url(self.cmain.cview.get_logging_path())
		n_rows, errors = generate_ids(self)
		self.cmain.cview.progress.stop()
		self.cmain.cview.show_notification(
			'''Generated Arch14CZ IDs with %d errors.<br>(see <a href="%s">Log File</a> for details)''' % (
				len(errors), path_log
			)
		)
		self.cmain.cview.log_message(
			"Generated Arch14CZ IDs.\nError Messages:\n%s" % (
				"\n".join(errors)
			)
		)
		self._model.blockSignals(False)
		self.on_changed([],[])
	
	def import_excel(self, path, fields):
		# fields[name] = column index
		
		path_log = as_url(self.cmain.cview.get_logging_path())
		
		self.cmain.cview.progress.show("Importing")
		n_imported, n_rows, errors = import_xlsx(self, path, fields, self.cmain.cview.progress)
		self.cmain.cview.progress.stop()
		self.cmain.cview.show_notification(
			'''Imported %d/%d rows with %d errors.<br>(see <a href="%s">Log File</a> for details)''' % (
				n_imported, n_rows, len(errors), path_log
			), delay = 7000
		)
		self.cmain.cview.log_message(
			"Imported %d/%d rows.\nError Messages:\n%s" % (
				n_imported, n_rows, "\n".join(errors)
			)
		)
	
	def get_cal_curve(self):
		
		return self._cal_curve
	
	def set_cal_curve(self, path):
		
		self._cal_curve = path
	
	def vis_dating_order(self, detailed = False):
		
		vis_order(self, detailed)
	
	
	# ---- Deposit
	# ------------------------------------------------------------------------
	def update_model_info(self):
		
		self.cmain.cview.set_title(self.get_datasource_name())
		self.cmain.cview.set_db_name("%s (%s)" % (
			self.get_datasource_name(),
			str(self.get_datasource()),
		))
		
		path = self.get_folder()
		url = as_url(path)
		if isinstance(self.get_datasource(), Memory):
			path = "temporary"
		self.cmain.cview.set_folder(path, url)
		
		host = self.get_frontend_host()
		name = self.get_frontend_name()
		if not name:
			host = "not connected"
			name = "not connected"
		self.cmain.cview.set_frontend_host(host)
		self.cmain.cview.set_frontend_name(name)
		self.cmain.cview.set_publish_enabled(self.has_frontend())
		
	def update_recent(self, kwargs):
		
		datasource = kwargs.get("datasource", None)
		if isinstance(datasource, AbstractDatasource):
			kwargs.update(datasource.to_dict())
		
		url = kwargs.get("url", None)
		if not url:
			path = kwargs.get("path", None)
			if path:
				url = as_url(path)
		self.cmain.cview._view.add_recent_connection(
			url = url,
			identifier = kwargs.get("identifier", None),
			connstr = kwargs.get("connstr", None),
		)
	
	def load(self, *args, **kwargs):
		# datasource = Datasource or format
		
		if not self.cmain.check_save():
			return False
		
		return DCModel.load(self, *args, **kwargs)

