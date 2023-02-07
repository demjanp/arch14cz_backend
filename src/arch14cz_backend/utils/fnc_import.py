from openpyxl import load_workbook
from copy import deepcopy

def import_xlsx(cmodel, path, fields, progress):
	# fields[name] = column index
	#
	# returns n_imported, n_rows, errors
	#	n_imported = number of rows imported
	#	n_rows = number of rows processed
	#	errors = [error message, ...]
	
	def get_from_field(name, fields, row):
		
		index = fields.get(name, -1)
		if index == -1:
			return ""
		value = row[index].value
		if value is None:
			return ""
		return str(value).strip()
	
	def find_or_add_obj(cls, data):
		
		obj = cmodel.find_object_with_descriptors([cls], data)
		if obj is None:
			obj = cmodel.add_object_with_descriptors(cls, data)
		return obj
	
	
	errors = []
	
	c14_data = []
	
	other_data = {
		"Site": [],				# [{Name, Location, Note}, ...]
		"Context": [],			# [{Name, Note, Description}, ...]
		"Source": [],			# [{Description, Reference, URI}, ...]
		"Activity_Area": [],	# [{Name}, ...]
		"Feature": [],			# [{Name}, ...]
		"Sample": [],			# [{Number}, ...]
		"Material": [],			# [{Name}, ...]
		"Reliability": [],		# [{Name}, ...]
		"C_14_Method": [],		# [{Name}, ...]
		"Country": [],			# [{Name}, ...]
		"District": [],			# [{Name}, ...]
		"Cadastre": [],			# [{Name}, ...]
	}
	
	relative_datings = []
	relative_datings_general = set([])  # without Relative Dating Note
	
	wb = load_workbook(filename = path, read_only = True)
	for sheet in wb.sheetnames:
		ws = wb[sheet]
		break
	n_rows = ws.max_row - 1
	unknown_sample_n = 1
	row_n = 1
	progress.update_state(value = row_n, maximum = n_rows * 2)
	for row in ws.iter_rows(min_row = 2):
		
		progress.update_state(value = row_n)
		if progress.cancel_pressed():
			return 0, n_rows, ["Cancelled by user"]
		
		row_n += 1
		row_data = {}
		
		c14_lab_code = get_from_field("C-14 Analysis Lab Code", fields, row)
		c14_activity = get_from_field("C-14 Analysis C-14 Activity BP", fields, row)
		c14_uncert = get_from_field("C-14 Analysis C-14 Uncert. 1 Sigma", fields, row)
		c14_date_type = get_from_field("Date Type", fields, row)
		row_data["C_14_Method"] = get_from_field("C-14 Analysis C-14 Method", fields, row)
		c14_note_1 = get_from_field("C-14 Analysis Note 1", fields, row)
		c14_delta13c = get_from_field("Delta C-13", fields, row)
		c14_note_2 = get_from_field("C-14 Analysis Note 2", fields, row)
		
		row_data["Country"] = get_from_field("Country", fields, row)
		row_data["District"] = get_from_field("District", fields, row)
		cadastre = get_from_field("Cadastre", fields, row)
		cadastre_code = get_from_field("Cadastre Code", fields, row)
		
		site_name = get_from_field("Site Name", fields, row)
		site_coordinates = get_from_field("Site Coordinates", fields, row)
		site_note = get_from_field("Site Note", fields, row)
		amcr_id = get_from_field("AMCR ID", fields, row)
		
		row_data["Activity_Area"] = get_from_field("Activity Area", fields, row)
		
		feature = get_from_field("Feature", fields, row)
		
		context_name = get_from_field("Context Name", fields, row)
		context_description = get_from_field("Context Description", fields, row)
		depth_cm = get_from_field("Depth cm", fields, row)
		
		relative_dating_name_1 = get_from_field("Relative Dating Name1", fields, row)
		relative_dating_note_1 = get_from_field("Relative Dating Note1", fields, row)
		relative_dating_name_2 = get_from_field("Relative Dating Name2", fields, row)
		relative_dating_note_2 = get_from_field("Relative Dating Note2", fields, row)
		
		row_data["Sample"] = get_from_field("Sample Number", fields, row)
		sample_note = get_from_field("Sample Note", fields, row)
		
		row_data["Material"] = get_from_field("Material Name", fields, row)
		material_note = get_from_field("Material Note", fields, row)
		
		row_data["Reliability"] = get_from_field("Reliability", fields, row)
		reliability_note = get_from_field("Reliability Note", fields, row)
		
		source_description = get_from_field("Source Description", fields, row)
		source_reference = get_from_field("Source Reference", fields, row)
		source_uri = get_from_field("Source URI", fields, row)
		source_acquisition = get_from_field("Source Acquisition", fields, row)
		
		if c14_date_type != "conv. 14C BP":
			continue
		
		try:
			c14_activity = float(c14_activity)
		except:
			errors.append("Invalid Entry: Row %d, C-14 Analysis C-14 Activity BP: %s" % (row_n, str(c14_activity)))
			continue
		try:
			c14_uncert = float(c14_uncert)
		except:
			errors.append("Invalid Entry: Row %d, C-14 Analysis C-14 Uncert. 1 Sigma: %s" % (row_n, str(c14_uncert)))
			continue
		if c14_delta13c:
			try:
				c14_delta13c = float(c14_delta13c)
			except:
				errors.append("Invalid Entry: Row %d, Delta C-13: %s" % (row_n, c14_delta13c))
				continue
		
		c14_note_analysis = "; ".join([val for val in [c14_note_1, c14_note_2] if val])
		
		relative_datings_row = []
		for name, note in [[relative_dating_name_1, relative_dating_note_1], [relative_dating_name_2, relative_dating_note_2]]:
			if name:
				relative_datings_general.add(name)
				if note:
					relative_datings_row.append("%s, %s" % (name, note))
				else:
					relative_datings_row.append(name)
		
		row_data["Site"] = {
			"Name": site_name,
			"Location": site_coordinates,
			"Note": site_note,
		}
		# TODO amcr_id
		
		if not context_name:
			context_name = "unspecified"
		row_data["Context"] = {
			"Name": "%s, %s" % (site_name, context_name),
			"Description": context_description,
			"Depth": depth_cm,
		}
		
		row_data["Feature"] = {
			"Name": feature,
		}
		
		if row_data["Sample"] == "":
			row_data["Sample"] = "unknown %d" % (unknown_sample_n)
			unknown_sample_n += 1
		row_data["Sample"] = "%s-%s" % (site_name, row_data["Sample"])
		
		row_data["Activity_Area"] = {"Name": row_data["Activity_Area"]}
		row_data["Sample"] = {"Number": row_data["Sample"]}
		row_data["Material"] = {"Name": row_data["Material"]}
		row_data["Reliability"] = {"Name": row_data["Reliability"]}
		row_data["C_14_Method"] = {"Name": row_data["C_14_Method"]}
		row_data["Country"] = {"Name": row_data["Country"]}
		row_data["District"] = {"Name": row_data["District"]}
		row_data["Cadastre"] = {
			"Name": cadastre,
			"Code": cadastre_code,
		}
		
		row_idxs = {}
		for key in row_data:
			if row_data[key] in other_data[key]:
				row_idxs[key] = other_data[key].index(row_data[key])
			else:
				other_data[key].append(deepcopy(row_data[key]))
				row_idxs[key] = len(other_data[key]) - 1
		
		sources_row = [
			{
				"Description": source_description,
				"Reference": source_reference,
				"URI": source_uri,
			},
			{
				"Description": source_acquisition,
				"Reference": "",
				"URI": "",
			},			
		]
		for data in sources_row:
			if data in other_data["Source"]:
				row_idxs["Source"] = other_data["Source"].index(data)
			else:
				other_data["Source"].append(deepcopy(data))
				row_idxs["Source"] = len(other_data["Source"]) - 1
		
		relative_dating_idxs = []
		for name in relative_datings_row:
			if name in relative_datings:
				relative_dating_idxs.append(relative_datings.index(name))
			else:
				relative_datings.append(name)
				relative_dating_idxs.append(len(relative_datings) - 1)
		
		c_14_analysis = {
			"Lab_Code": c14_lab_code,
			"C_14_Activity_BP": c14_activity,
			"C_14_Uncertainty_1Sig": c14_uncert,
			"Delta_C_13_per_mil": c14_delta13c,
			"Note_Analysis": c14_note_analysis,
			"Note_Material": material_note,
			"Note_Sample": sample_note,
			"Note_Reliability": reliability_note,
		}
		c14_data.append([deepcopy(c_14_analysis), deepcopy(row_idxs), deepcopy(relative_dating_idxs)])
	
	relative_datings_to_add = sorted(list(relative_datings_general.difference(relative_datings)))
	
	cls_lookup = {}
	for cls_name in ["C_14_Analysis", "Relative_Dating"] + list(other_data.keys()):
		cls_lookup[cls_name] = cmodel.add_class(cls_name)
	cls_lookup["Source"].add_relation("C_14_Analysis", "describes")
	cls_lookup["C_14_Analysis"].add_relation("Reliability", "descr")
	cls_lookup["C_14_Analysis"].add_relation("C_14_Method", "descr")
	cls_lookup["C_14_Analysis"].add_relation("Sample", "analyses")
	cls_lookup["Sample"].add_relation("Material", "descr")
	cls_lookup["Context"].add_relation("Sample", "contains")
	cls_lookup["Context"].add_relation("Feature", "descr")
	cls_lookup["Site"].add_relation("Context", "contains")
	cls_lookup["Context"].add_relation("Activity_Area", "descr")
	cls_lookup["Cadastre"].add_relation("Site", "contains")
	cls_lookup["District"].add_relation("Cadastre", "contains")
	cls_lookup["Country"].add_relation("District", "contains")
	cls_lookup["Relative_Dating"].add_relation("Context", "dates")
	
	obj_lookup = dict([(cls_name, {}) for cls_name in other_data]) # {cls_name: {idx: Object, ...}, ...}
	obj_lookup["Relative_Dating"] = {}
	
	cls = cls_lookup["Relative_Dating"]
	for idx, name in enumerate(relative_datings):
		obj_lookup["Relative_Dating"][idx] = find_or_add_obj(cls, {"Name": name})
	for name in relative_datings_to_add:
		find_or_add_obj(cls, {"Name": name})
	
	for cls_name in other_data:
		for idx, data in enumerate(other_data[cls_name]):
			obj_lookup[cls_name][idx] = find_or_add_obj(cls_lookup[cls_name], data)
	
	for c_14_analysis, other_idxs, relative_dating_idxs in c14_data:
		
		row_n += 1
		progress.update_state(value = row_n)
		if progress.cancel_pressed():
			return 0, n_rows, ["Cancelled by user"]
		
		obj_c_14 = find_or_add_obj(cls_lookup["C_14_Analysis"], c_14_analysis)
		
		obj_site = obj_lookup["Site"][other_idxs["Site"]]
		obj_context = obj_lookup["Context"][other_idxs["Context"]]
		obj_source = obj_lookup["Source"][other_idxs["Source"]]
		obj_feature = obj_lookup["Feature"][other_idxs["Feature"]]
		obj_activity_area = obj_lookup["Activity_Area"][other_idxs["Activity_Area"]]
		obj_sample = obj_lookup["Sample"][other_idxs["Sample"]]
		obj_material = obj_lookup["Material"][other_idxs["Material"]]
		obj_reliability = obj_lookup["Reliability"][other_idxs["Reliability"]]
		obj_method = obj_lookup["C_14_Method"][other_idxs["C_14_Method"]]
		obj_country = obj_lookup["Country"][other_idxs["Country"]]
		obj_district = obj_lookup["District"][other_idxs["District"]]
		obj_cadastre = obj_lookup["Cadastre"][other_idxs["Cadastre"]]
		
		obj_source.add_relation(obj_c_14, "describes")
		obj_c_14.add_relation(obj_reliability, "descr")
		obj_c_14.add_relation(obj_method, "descr")
		obj_c_14.add_relation(obj_sample, "analyses")
		obj_sample.add_relation(obj_material, "descr")
		obj_context.add_relation(obj_sample, "contains")
		obj_context.add_relation(obj_feature, "descr")
		obj_site.add_relation(obj_context, "contains")
		obj_context.add_relation(obj_activity_area, "descr")
		obj_cadastre.add_relation(obj_site, "contains")
		obj_district.add_relation(obj_cadastre, "contains")
		obj_country.add_relation(obj_district, "contains")
		
		for idx in relative_dating_idxs:
			obj_lookup["Relative_Dating"][idx].add_relation(obj_context, "dates")
	
	progress.stop()
	
	return len(c14_data), n_rows, errors
