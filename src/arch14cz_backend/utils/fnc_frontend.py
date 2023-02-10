from deposit.utils.fnc_serialize import (try_numeric)
from arch14cz_backend.utils.fnc_radiocarbon import (
	load_calibration_curve, calibrate, calc_range
)
from arch14cz_backend.utils.fnc_phasing import (get_phasing)

from collections import defaultdict
from datetime import datetime
import psycopg2
import time
import sys
import os

def update_port(frontend_connection):
	
	out = dict(
		host = "",
		port = 5432,
		dbname = "",
		schema = "public",
		user = "",
		password = "",
	)
	out.update(frontend_connection)
	host = frontend_connection.get("host", None)
	if host is None:
		return out
	host = host.split(":")
	if len(host) != 2:
		return out
	host, port = host
	port = try_numeric(port)
	if not isinstance(port, int):
		return out
	out["port"] = port
	out["host"] = host
	return out

def check_connection(
		host = "",
		dbname = "",
		schema = "public",
		user = "",
		password = ""
	):
		
		host = host.split(":")
		if len(host) != 2:
			return "Port not specified"
		host, port = host
		port = try_numeric(port)
		if not isinstance(port, int):
			return "Invalid port specified: %s" % (str(port))
		try:
			conn = psycopg2.connect(
				dbname = dbname, user = user, password = password, 
				host = host, port = port
			)
		except:
			_, exc_value, _ = sys.exc_info()
			return str(exc_value)
		
		return True

def publish_data(cmodel, frontend_connection, path_curve, progress):
	
	def float_or_none(value):
		
		value = try_numeric(value)
		if not (isinstance(value, int) or isinstance(value, float)):
			return None
		return float(value)
	
	def str_or_empty(value):
		
		if value is None:
			return ""
		return str(value)
	
	errors = []
	n_published = 0
	n_rows = 0
	
	if "" in list(frontend_connection.values()):
		return n_published, n_rows, ["Invalid connection specified"]
	
	if not os.path.isfile(path_curve):
		return n_published, n_rows, ["Calibration Curve file not found"]
	
	progress.update_state(text = "Calculating order for relative dates")
	phasing, names, circulars = get_phasing(cmodel)
	# phasing = {obj_id: [phase_min, phase_max], ...}
	#	phase_min/max = None if no chronological relations found
	# names = {obj_id: name, ...}
	# circulars = [obj_id, ...]
	
	def cancel_progress(n_published, n_rows, errors):
		
		cmodel._model.blockSignals(False)
		cmodel.on_changed([],[])
		return n_published, n_rows, errors
	
	cmodel._model.blockSignals(True)
	
	if circulars:
		errors = ["Circular relations found between the following datings:"]
		for obj_id in circulars:
			errors.append("\t%s" % (names[obj_id]))
		return cancel_progress(n_published, n_rows, errors)
	
	cls = cmodel.get_class("Relative_Dating")
	if cls is None:
		return cancel_progress(n_published, n_rows, ["Relative_Dating Class not found"])
	for obj in cls.get_members(direct_only = True):
		if progress.cancel_pressed():
			return cancel_progress(n_published, n_rows, ["Cancelled by user"])
		phase_min, phase_max = phasing[obj.id]
		obj.set_descriptor("Order_Min", phase_min)
		obj.set_descriptor("Order_Max", phase_max)
	
	progress.update_state(text = "Generating Arch14CZ_ID for each record")
	arch_ids = set([])
	cls_c14 = cmodel.get_class("C_14_Analysis")
	if cls_c14 is None:
		return cancel_progress(n_published, n_rows, ["C_14_Analysis Class not found"])
	for obj in cls_c14.get_members(direct_only = True):
		n_rows += 1
		arch_id = obj.get_descriptor("Arch14CZ_ID")
		if arch_id is not None:
			arch_ids.add(arch_id)
	datestr = datetime.now().strftime("%d-%m-%Y")
	for obj in cls_c14.get_members(direct_only = True):
		if progress.cancel_pressed():
			return cancel_progress(n_published, n_rows, ["Cancelled by user"])
		arch_id = obj.get_descriptor("Arch14CZ_ID")
		if arch_id is None:
			n = 0
			while True:
				arch_id = "A14CZ_%s_%d" % (datestr, n)
				if arch_id not in arch_ids:
					break
				n += 1
			obj.set_descriptor("Arch14CZ_ID", arch_id)
			arch_ids.add(arch_id)
	
	progress.update_state(text = "Calibrating C-14 dates")
	curve = load_calibration_curve(path_curve, interpolate = False)
	cnt = 1
	cmax = 3*n_rows + 30
	for obj in cls_c14.get_members(direct_only = True):
		progress.update_state(value = cnt, maximum = cmax)
		if progress.cancel_pressed():
			return cancel_progress(n_published, n_rows, ["Cancelled by user"])
		cnt += 1
		ce_from = obj.get_descriptor("CE_From")
		ce_to = obj.get_descriptor("CE_To")
		if (ce_from is not None) and (ce_to is not None):
			continue
		age = float_or_none(obj.get_descriptor("C_14_Activity_BP"))
		uncert = float_or_none(obj.get_descriptor("C_14_Uncertainty_1Sig"))
		if (age is None) or (uncert is None):
			continue
		dist = calibrate(age, uncert, curve[:,1], curve[:,2])
		ce_to, ce_from = calc_range(curve[:,0], dist, 0.9545)
		ce_from, ce_to = int(round(-(ce_from - 1950))), int(round(-(ce_to - 1950)))
		obj.set_descriptor("CE_From", ce_from)
		obj.set_descriptor("CE_To", ce_to)
	
	progress.update_state(text = "Creating tables", value = cnt, maximum = cmax)
	table_main = "c_14_main"
	table_country = "c_14_dict_country"
	table_district = "c_14_dict_district"
	table_cadastre = "c_14_dict_cadastre"
	table_activity_area = "c_14_dict_activity_area"
	table_feature = "c_14_dict_feature"
	table_material = "c_14_dict_material"
	table_relative_dating = "c_14_dict_relative_dating"
	
	frontend_connection = update_port(frontend_connection)
	schema = frontend_connection["schema"]
	del frontend_connection["schema"]
	try:
		conn = psycopg2.connect(**frontend_connection)
	except:
		_, exc_value, _ = sys.exc_info()
		return cancel_progress(n_published, n_rows, [str(exc_value)])
	cursor = conn.cursor()
	cursor.execute(
		"SELECT table_name FROM information_schema.tables WHERE table_schema = '%s';" % (schema)
	)
	tables = [row[0] for row in cursor.fetchall()]
	table_names = set([
		table_main, table_country, table_district, table_cadastre, 
		table_activity_area, table_feature, table_material, table_relative_dating,
	])
	for name in table_names:
		cnt += 1
		progress.update_state(value = cnt, maximum = cmax)
		if progress.cancel_pressed():
			return cancel_progress(n_published, n_rows, ["Cancelled by user"])
		if name in tables:
			cursor.execute("DROP TABLE IF EXISTS \"%s\";" % (name))
	
	# wait until tables are deleted
	conn.commit()
	while True:
		cursor = conn.cursor()
		cursor.execute(
			"SELECT table_name FROM information_schema.tables WHERE table_schema = '%s';" % (schema)
		)
		tables = set([row[0] for row in cursor.fetchall()])
		if (not tables) or (not tables.issubset(table_names)):
			break
		if progress.cancel_pressed():
			return cancel_progress(n_published, n_rows, ["Cancelled by user"])
		time.sleep(0.5)
	
	if table_main not in tables:
		cursor.execute('''CREATE TABLE %s (
			"Arch14CZ_ID" TEXT,
			"C_14_Lab_Code" TEXT,
			"C_14_Activity" REAL,
			"C_14_Uncertainty" REAL,
			"C_14_CE_From" INTEGER,
			"C_14_CE_To" INTEGER,
			"C_14_Note" TEXT,
			"Reliability" TEXT,
			"Reliability_Note" TEXT,
			"Country" TEXT,
			"Country_Code" TEXT,
			"District" TEXT,
			"Cadastre" TEXT,
			"Site" TEXT,
			"Coordinates" TEXT,
			"Context_Name" TEXT,
			"Context_Description" TEXT,
			"Context_Depth" TEXT,
			"Activity_Area" TEXT,
			"Feature" TEXT,
			"Relative_Dating_Name" TEXT,
			"Relative_Dating_Order" INTEGER[],
			"Sample_Number" TEXT,
			"Sample_Note" TEXT,
			"Material" TEXT,
			"Material_Note" TEXT,
			"Source" TEXT,
			PRIMARY KEY ("Arch14CZ_ID")
		);''' % (table_main))
	for name in [table_country, table_activity_area, table_feature, table_material]:
		cnt += 1
		progress.update_state(value = cnt, maximum = cmax)
		if progress.cancel_pressed():
			return cancel_progress(n_published, n_rows, ["Cancelled by user"])
		if name not in tables:
			cursor.execute('''CREATE TABLE %s (
				"Name" TEXT
			);''' % (name))
	for name in [table_district, table_cadastre]:
		cnt += 1
		progress.update_state(value = cnt, maximum = cmax)
		if progress.cancel_pressed():
			return cancel_progress(n_published, n_rows, ["Cancelled by user"])
		if name not in tables:
			cursor.execute('''CREATE TABLE %s (
				"Code" TEXT,
				"Name" TEXT
			);''' % (name))
	if table_relative_dating not in tables:
		cursor.execute('''CREATE TABLE %s (
			"Code" TEXT,
			"Name" TEXT
		);''' % (table_relative_dating))
	cnt += 1
	progress.update_state(value = cnt, maximum = cmax)
	if progress.cancel_pressed():
		return cancel_progress(n_published, n_rows, ["Cancelled by user"])
	
	# wait until tables are created on server
	conn.commit()
	tables = set([])
	while not tables.issubset(table_names):
		cursor = conn.cursor()
		cursor.execute(
			"SELECT table_name FROM information_schema.tables WHERE table_schema = '%s';" % (schema)
		)
		tables = set([row[0] for row in cursor.fetchall()])
		if progress.cancel_pressed():
			return cancel_progress(n_published, n_rows, ["Cancelled by user"])
		time.sleep(0.5)
	
	progress.update_state(text = "Collecting data", value = cnt, maximum = cmax)
	
	dict_country = set([])
	dict_district = set([])
	dict_cadastre = set([])
	dict_activity_area = set([])
	dict_feature = set([])
	dict_material = set([])
	dict_relative_dating = set([])
	
	lookup_Sample = {}  # {obj_id: Number, ...}
	lookup_Context = {}  # {obj_id: {Name, Description, Depth}, ...}
	lookup_Site = {}  # {obj_id: {Name, Location}, ...}
	lookup_CountryDistrictCadastre = {} 
		# {obj_id: {Country, Country_Code, District, Cadastre}, ...}
	query = cmodel.get_query(
		"SELECT C_14_Analysis.Arch14CZ_ID, Sample.Number, \
			Context.Name, Context.Description, Context.Depth, \
			Site.Name, Site.Location, Cadastre.Name, District.Name, Country.Name",
		silent = True
	)
	for row in range(len(query)):
		progress.update_state(value = cnt, maximum = cmax)
		if progress.cancel_pressed():
			return cancel_progress(n_published, n_rows, ["Cancelled by user"])
		cnt += 1
		
		obj_id = query[row, "C_14_Analysis", "Arch14CZ_ID"][0]
		lookup_Sample[obj_id] = str_or_empty(query[row, "Sample", "Number"][1])
		lookup_Context[obj_id] = {
			"Name": str_or_empty(query[row, "Context", "Name"][1]), 
			"Description": str_or_empty(query[row, "Context", "Description"][1]), 
			"Depth": str_or_empty(query[row, "Context", "Depth"][1])
		}
		lookup_Site[obj_id] = {
			"Name": str_or_empty(query[row, "Site", "Name"][1]),
			"Location": str_or_empty(query[row, "Site", "Location"][1])
		}
		lookup_CountryDistrictCadastre[obj_id] = {
			"Country": str_or_empty(query[row, "Country", "Name"][1]),
			"Country_Code": str_or_empty(query[row, "Country", "Name"][0]),
			"District": str_or_empty(query[row, "District", "Name"][1]),
			"Cadastre": str_or_empty(query[row, "Cadastre", "Name"][1]),
		}
		dict_country.add(lookup_CountryDistrictCadastre[obj_id]["Country"])
		dict_district.add((
			lookup_CountryDistrictCadastre[obj_id]["District"], 
			lookup_CountryDistrictCadastre[obj_id]["Country_Code"]
		))
		dict_cadastre.add((
			lookup_CountryDistrictCadastre[obj_id]["Cadastre"], 
			lookup_CountryDistrictCadastre[obj_id]["District"], 
			lookup_CountryDistrictCadastre[obj_id]["Country_Code"]
		))
	
	lookup_Reliability = {}   # {obj_id: Name, ...}
	query = cmodel.get_query(
		"SELECT C_14_Analysis.Arch14CZ_ID, Reliability.Name",
		silent = True
	)
	for row in range(len(query)):
		lookup_Reliability[query[row, "C_14_Analysis", "Arch14CZ_ID"][0]] = \
			str_or_empty(query[row, "Reliability", "Name"][1])
	cnt += 1
	progress.update_state(value = cnt, maximum = cmax)
	if progress.cancel_pressed():
		return cancel_progress(n_published, n_rows, ["Cancelled by user"])
	
	lookup_Activity_Area = {}   # {obj_id: Name, ...}
	query = cmodel.get_query(
		"SELECT C_14_Analysis.Arch14CZ_ID, Activity_Area.Name", silent = True
	)
	for row in range(len(query)):
		value = str_or_empty(query[row, "Activity_Area", "Name"][1])
		lookup_Activity_Area[query[row, "C_14_Analysis", "Arch14CZ_ID"][0]] = value
		dict_activity_area.add(value)
	cnt += 1
	progress.update_state(value = cnt, maximum = cmax)
	if progress.cancel_pressed():
		return cancel_progress(n_published, n_rows, ["Cancelled by user"])
	
	lookup_Feature = {}   # {obj_id: Name, ...}
	query = cmodel.get_query(
		"SELECT C_14_Analysis.Arch14CZ_ID, Feature.Name", silent = True
	)
	for row in range(len(query)):
		value = str_or_empty(query[row, "Feature", "Name"][1])
		lookup_Feature[query[row, "C_14_Analysis", "Arch14CZ_ID"][0]] = value
		dict_feature.add(value)
	cnt += 1
	progress.update_state(value = cnt, maximum = cmax)
	if progress.cancel_pressed():
		return cancel_progress(n_published, n_rows, ["Cancelled by user"])
	
	lookup_Material = {}   # {obj_id: Name, ...}
	query = cmodel.get_query(
		"SELECT C_14_Analysis.Arch14CZ_ID, Material.Name", silent = True
	)
	for row in range(len(query)):
		value = str_or_empty(query[row, "Material", "Name"][1])
		lookup_Material[query[row, "C_14_Analysis", "Arch14CZ_ID"][0]] = value
		dict_material.add(value)
	cnt += 1
	progress.update_state(value = cnt, maximum = cmax)
	if progress.cancel_pressed():
		return cancel_progress(n_published, n_rows, ["Cancelled by user"])
	
	lookup_Source = defaultdict(list)  # {obj_id: [{Description, URI, Reference}, ...], ...}
	query = cmodel.get_query(
		"SELECT C_14_Analysis.Arch14CZ_ID, \
			Source.Description, Source.URI, Source.Reference",
		silent = True
	)
	for row in range(len(query)):
		lookup_Source[query[row, "C_14_Analysis", "Arch14CZ_ID"][0]].append({
			"Description": str_or_empty(query[row, "Source", "Description"][1]),
			"URI": str_or_empty(query[row, "Source", "URI"][1]),
			"Reference": str_or_empty(query[row, "Source", "Reference"][1]),
		})
	cnt += 1
	progress.update_state(value = cnt, maximum = cmax)
	if progress.cancel_pressed():
		return cancel_progress(n_published, n_rows, ["Cancelled by user"])
	
	lookup_Relative_Dating = defaultdict(list)  # {obj_id: [{Name, Order_Min, Order_Max}, ...], ...}
	query = cmodel.get_query(
		"SELECT C_14_Analysis.Arch14CZ_ID, Relative_Dating.Name, \
			Relative_Dating.Order_Min, Relative_Dating.Order_Max",
		silent = True
	)
	for row in range(len(query)):
		lookup_Relative_Dating[query[row, "C_14_Analysis", "Arch14CZ_ID"][0]].append({
			"Name": str_or_empty(query[row, "Relative_Dating", "Name"][1]),
			"Order_Min": str_or_empty(query[row, "Relative_Dating", "Order_Min"][1]),
			"Order_Max": str_or_empty(query[row, "Relative_Dating", "Order_Max"][1]),
		})
	cnt += 1
	progress.update_state(value = cnt, maximum = cmax)
	if progress.cancel_pressed():
		return cancel_progress(n_published, n_rows, ["Cancelled by user"])
	
	query = cmodel.get_query(
		"SELECT Relative_Dating.Name, Relative_Dating.Order_Min, Relative_Dating.Order_Max",
		silent = True
	)
	for row in range(len(query)):
		name = str_or_empty(query[row, "Relative_Dating", "Name"][1])
		order_min = str_or_empty(query[row, "Relative_Dating", "Order_Min"][1])
		order_max = str_or_empty(query[row, "Relative_Dating", "Order_Max"][1])
		if order_min and order_max:
			dict_relative_dating.add((name, int(order_min), int(order_max)))
	cnt += 1
	progress.update_state(value = cnt, maximum = cmax)
	if progress.cancel_pressed():
		return cancel_progress(n_published, n_rows, ["Cancelled by user"])
	
	progress.update_state(text = "Storing data", value = cnt, maximum = cmax)
	
	dict_country = sorted(list(dict_country))
	dict_district = sorted(list(dict_district))
	dict_cadastre = sorted(list(dict_cadastre))
	dict_activity_area = sorted(list(dict_activity_area))
	dict_feature = sorted(list(dict_feature))
	dict_material = sorted(list(dict_material))
	dict_relative_dating = sorted(
		list(dict_relative_dating), key = lambda row: row[1]
	)
	
	for name, data in [
		(table_country, dict_country),
		(table_activity_area, dict_activity_area),
		(table_feature, dict_feature), 
		(table_material, dict_material),
	]:
		cnt += 1
		progress.update_state(value = cnt, maximum = cmax)
		if progress.cancel_pressed():
			return cancel_progress(n_published, n_rows, ["Cancelled by user"])
		for value in data:
			if value:
				cursor.execute("INSERT INTO %s VALUES (%%s);" % (name), (value,))
	
	cnt += 1
	progress.update_state(value = cnt, maximum = cmax)
	if progress.cancel_pressed():
		return cancel_progress(n_published, n_rows, ["Cancelled by user"])
	for district, country_code in dict_district:
		if district:
			code = "%s#%s" % (district, country_code)
			label = "%s (%s)" % (district, country_code)
			cursor.execute("INSERT INTO %s VALUES (%%s, %%s);" % (table_district), (code, label))
	
	cnt += 1
	progress.update_state(value = cnt, maximum = cmax)
	if progress.cancel_pressed():
		return cancel_progress(n_published, n_rows, ["Cancelled by user"])
	for cadastre, district, country_code in dict_cadastre:
		if cadastre:
			code = "%s#%s#%s" % (cadastre, district, country_code)
			label = "%s (%s, %s)" % (cadastre, district, country_code)
			cursor.execute("INSERT INTO %s VALUES (%%s, %%s);" % (table_cadastre), (code, label))
	
	cnt += 1
	progress.update_state(value = cnt, maximum = cmax)
	if progress.cancel_pressed():
		return cancel_progress(n_published, n_rows, ["Cancelled by user"])
	for name, order_min, order_max in dict_relative_dating:
		code = "%d#%d" % (order_min, order_max)
		cursor.execute("INSERT INTO %s VALUES (%%s, %%s);" % (table_relative_dating), (code, name))
	
	n_published = 0
	for obj in cls_c14.get_members(direct_only = True):
		
		cnt += 1
		progress.update_state(value = cnt, maximum = cmax)
		if progress.cancel_pressed():
			return cancel_progress(n_published, n_rows, ["Cancelled by user"])
		
		obj_id = obj.id
		vC_14_Activity = float_or_none(obj.get_descriptor("C_14_Activity_BP"))
		vC_14_Uncertainty = float_or_none(obj.get_descriptor("C_14_Uncertainty_1Sig"))
		if (vC_14_Activity is None) or (vC_14_Uncertainty is None):
			continue
		
		vArch14CZ_ID = obj.get_descriptor("Arch14CZ_ID")
		vC_14_Lab_Code = obj.get_descriptor("Lab_Code")
		vC_14_CE_From = int(obj.get_descriptor("CE_From"))
		vC_14_CE_To = int(obj.get_descriptor("CE_To"))
		vC_14_Note = str_or_empty(obj.get_descriptor("Note_Analysis"))
		vReliability = lookup_Reliability[obj_id] if obj_id in lookup_Reliability else ""
		vReliability_Note = str_or_empty(obj.get_descriptor("Note_Reliability"))
		if obj_id in lookup_CountryDistrictCadastre:
			vCountry = lookup_CountryDistrictCadastre[obj_id]["Country"]
			vCountryCode = lookup_CountryDistrictCadastre[obj_id]["Country_Code"]
			vDistrict = lookup_CountryDistrictCadastre[obj_id]["District"]
			vCadastre = lookup_CountryDistrictCadastre[obj_id]["Cadastre"]
		vSite = lookup_Site[obj_id]["Name"] if obj_id in lookup_Site else ""
		vCoordinates = lookup_Site[obj_id]["Location"] if obj_id in lookup_Site else ""
		vContext_Name = lookup_Context[obj_id]["Name"] if obj_id in lookup_Context else ""
		vContext_Description = lookup_Context[obj_id]["Description"] if obj_id in lookup_Context else ""
		vContext_Depth = lookup_Context[obj_id]["Depth"] if obj_id in lookup_Context else ""
		vActivity_Area = lookup_Activity_Area[obj_id] if obj_id in lookup_Activity_Area else ""
		vFeature = lookup_Feature[obj_id] if obj_id in lookup_Feature else ""
		vSample_Number = lookup_Sample[obj_id] if obj_id in lookup_Sample else ""
		vSample_Note = str_or_empty(obj.get_descriptor("Note_Sample"))
		vMaterial = lookup_Material[obj_id] if obj_id in lookup_Material else ""
		vMaterial_Note = str_or_empty(obj.get_descriptor("Note_Material"))
		vSource = []
		for row in lookup_Source[obj_id]:
			vSource.append(", ".join([value for value in [
				row["Description"], row["URI"], row["Reference"]
			] if value]))
		vSource = "\n".join(vSource)
		vRelative_Dating_Name = []
		vRelative_Dating_Order = set([])
		for row in lookup_Relative_Dating[obj_id]:
			vRelative_Dating_Name.append(row["Name"])
			order_min, order_max = row["Order_Min"], row["Order_Max"]
			if order_min and order_max:
				vRelative_Dating_Order.update(
					list(range(int(order_min), int(order_max) + 1))
				)
		vRelative_Dating_Name = "; ".join(vRelative_Dating_Name)
		vRelative_Dating_Order = sorted(list(vRelative_Dating_Order))
		
		cursor.execute("INSERT INTO %s VALUES (%s);" % (table_main, ", ".join(["%s"]*27)), (
			vArch14CZ_ID,
			vC_14_Lab_Code,
			vC_14_Activity,
			vC_14_Uncertainty,
			vC_14_CE_From,
			vC_14_CE_To,
			vC_14_Note,
			vReliability,
			vReliability_Note,
			vCountry,
			vCountryCode,
			vDistrict,
			vCadastre,
			vSite,
			vCoordinates,
			vContext_Name,
			vContext_Description,
			vContext_Depth,
			vActivity_Area,
			vFeature,
			vRelative_Dating_Name,
			vRelative_Dating_Order,
			vSample_Number,
			vSample_Note,
			vMaterial,
			vMaterial_Note,
			vSource,
		))
		n_published += 1
	
	conn.commit()
	conn.close()
	
	return cancel_progress(n_published, n_rows, errors)

