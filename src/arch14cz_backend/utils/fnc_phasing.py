import numpy as np
import networkx as nx
from matplotlib import pyplot

def update_datings(cmodel):
	# cmodel = Deposit GUI DCModel
	# for each relative dating in format "[culture], [phase]", add a relation
	# [culture] -> contains -> [culture], [phase]
	
	def to_general(name):
		
		if "," in name:
			name = name.split(",")[0].strip()
		return name
	
	cls = cmodel.get_class("Relative_Dating")
	if cls is None:
		return
	obj_lookup = {}
	general = set()
	detailed = set()
	for obj in cls.get_members(direct_only = True):
		name = obj.get_descriptor("Name").strip()
		if not name:
			continue
		obj_lookup[name] = obj
		if "," in name:
			detailed.add(name)
			general.add(to_general(name))
			obj.set_descriptor("General", 0)
		else:
			obj.set_descriptor("General", 1)
	for name in general:
		if name not in obj_lookup:
			obj_lookup[name] = cmodel.add_object_with_descriptors(cls, {"Name": name, "General": 1})
	for name in detailed:
		name_general = to_general(name)
		obj_lookup[name_general].add_relation(obj_lookup[name], "contains")

def get_phasing(cmodel, 
		dating_cls = "Relative_Dating", name_descr = "Name", general_descr = "General", 
		before_rel = "before", same_as_rel = "same_as", contains_rel = "contains",
		general_only = False
	):
	# cmodel = Deposit GUI DCModel
	# returns phasing, names, circulars
	# 	phasing = {obj_id: [phase_min, phase_max], ...}; phase_min/max = None if no chronological relations found
	# 	names = {obj_id: name, ...}
	#	circulars = [obj_id, ...]
	
	def extract_datings(cmodel, 
			dating_cls, name_descr, general_descr, 
			before_rel, contains_rel, general_only
		):
		# returns G = nx.DiGraph
		# G.nodes[obj_id]["name"] = dating name
		# G.edges() = [(obj_id1, obj_id2), ...]; obj_id1 -> before -> obj_id2
		
		G = nx.DiGraph()
		
		cls = cmodel.get_class(dating_cls)
		if cls is None:
			return G
		
		for obj in cls.get_members(direct_only = True):
			if general_only and (obj.get_descriptor(general_descr) != 1):
				continue
			G.add_node(obj.id, name = obj.get_descriptor(name_descr))
		for obj1 in cls.get_members(direct_only = True):
			if general_only and (obj1.get_descriptor(general_descr) != 1):
				continue
			objs1 = set([obj1.id])
			for obj, rel in obj1.get_relations():
				if rel != contains_rel:
					continue
				if general_only and (obj.get_descriptor(general_descr) != 1):
					continue
				objs1.add(obj.id)
			objs2 = set()
			for obj2, rel in obj1.get_relations():
				if rel != before_rel:
					continue
				if general_only and (obj2.get_descriptor(general_descr) != 1):
					continue
				objs2.add(obj2.id)
				for obj, rel in obj2.get_relations():
					if rel != contains_rel:
						continue
					if general_only and (obj.get_descriptor(general_descr) != 1):
						continue
					objs2.add(obj.id)
			if not objs2:
				continue
			for obj1_id in objs1:
				for obj2_id in objs2:
					G.add_edge(obj1_id, obj2_id)
		
		return G
	
	def find_circulars(chronostrat):
		# returns [idx, ...]; idx = index in chronostrat
		
		circulars = set([])
		G = nx.from_numpy_matrix(chronostrat, create_using = nx.DiGraph)
		for i, j in G.edges:
			if nx.has_path(G, j, i):
				circulars.add(i)
				circulars.add(j)
		
		return list(circulars)
	
	def get_lower_phasing(chronostrat):
		
		n_nodes = chronostrat.shape[0]
		phasing = np.full(n_nodes, np.nan)  # phasing[idx] = phase; lower = earlier
		
		# assign phase to nodes latest to earliest
		mask_todo = chronostrat.copy()
		phase = 0
		while mask_todo.any():
			latest = (mask_todo.any(axis = 0) & ~mask_todo.any(axis = 1))
			phasing[latest] = phase
			mask_todo[:,latest] = False
			phase += 1
		
		# assign phases to nodes earliest to latest, if not already assigned
		mask_todo = chronostrat.copy()
		phase = n_nodes
		while mask_todo.any():
			earliest = (mask_todo.any(axis = 1) & ~mask_todo.any(axis = 0))
			phasing[np.isnan(phasing) & earliest] = phase
			mask_todo[earliest] = False
			phase -= 1
		
		# minimize range of phases
		vals = np.unique(phasing[~np.isnan(phasing)])
		vals.sort()
		collect = phasing.copy()
		for val_new, val in enumerate(vals):
			collect[phasing == val] = val_new
		phasing = collect
		
		mask = (~np.isnan(phasing))
		if mask.any():
			phasing[mask] = phasing[mask].max() - phasing[mask]
		
		return phasing
	
	def get_phasing_limits(idx, phasing_lower, idxs_later, idxs_earlier):
		
		phase_min = 0
		ph_later = phasing_lower[idxs_later[idx]]
		ph_later = ph_later[~np.isnan(ph_later)]
		if ph_later.size:
			phase_max = int(ph_later.min()) - 1
		else:
			phase_max = phasing_lower.max()
		ph_earlier = phasing_lower[idxs_earlier[idx]]
		ph_earlier = ph_earlier[~np.isnan(ph_earlier)]
		if ph_earlier.size:
			phase_min = int(ph_earlier.max()) + 1
		if np.isnan(phase_max):
			phase_max = phase_min
		return int(phase_min), int(phase_max)
	
	G = extract_datings(cmodel, 
		dating_cls, name_descr, general_descr, 
		before_rel, contains_rel, general_only
	)
	
	nodes = sorted(list(G.nodes()))
	n_nodes = len(nodes)
	chronostrat = np.zeros((n_nodes, n_nodes), dtype = bool)
	for gi, gj in G.edges():
		chronostrat[nodes.index(gi), nodes.index(gj)] = True
	
	names = dict([(obj_id, G.nodes[obj_id]["name"]) for obj_id in G.nodes()])
	
	circulars = find_circulars(chronostrat)
	if circulars:
		circulars = [nodes[idx] for idx in circulars]
		return {}, names, circulars
	
	idxs_later = [np.where(chronostrat[idx])[0] for idx in range(n_nodes)]
	idxs_earlier = [np.where(chronostrat[:,idx])[0] for idx in range(n_nodes)]
	
	phasing_lower = get_lower_phasing(chronostrat)
	
	phasing = {}  # {obj_id: [phase_min, phase_max], ...}
	for idx in range(n_nodes):
		if (not chronostrat[idx].any()) and (not chronostrat[:,idx].any()):
			phase_min, phase_max = None, None
		else:
			phase_min, phase_max = get_phasing_limits(idx, phasing_lower, idxs_later, idxs_earlier)
		obj_id = nodes[idx]
		phasing[obj_id] = [phase_min, phase_max]
	
	for obj_id in phasing:
		if phasing[obj_id] == [None, None]:
			obj = cmodel.get_object(obj_id)
			for obj2, rel_ in obj.get_relations():
				if rel_ != same_as_rel:
					continue
				if phasing[obj2.id] != [None, None]:
					phasing[obj.id] = phasing[obj2.id].copy()
					break
	
	return phasing, names, circulars

def update_order(cmodel, progress = None):
	
	errors = []
	
	update_datings(cmodel)
	phasing, names, circulars = get_phasing(cmodel)
	# phasing = {obj_id: [phase_min, phase_max], ...}
	#	phase_min/max = None if no chronological relations found
	# names = {obj_id: name, ...}
	# circulars = [obj_id, ...]
	
	if circulars:
		errors = ["Circular relations found between the following datings:"]
		for obj_id in circulars:
			errors.append("\t%s" % (names[obj_id]))
		return errors
	
	cls = cmodel.get_class("Relative_Dating")
	if cls is None:
		return ["Relative_Dating Class not found"]
	for obj in cls.get_members(direct_only = True):
		if (progress is not None) and progress.cancel_pressed():
			return ["Cancelled by user"]
		phase_min, phase_max = phasing[obj.id]
		obj.set_descriptor("Order_Min", phase_min)
		obj.set_descriptor("Order_Max", phase_max)
	
	return errors

def vis_order(cmodel, detailed = False):
	
	phasing, names, circulars = get_phasing(cmodel, general_only = not detailed)
	# phasing = {obj_id: [phase_min, phase_max], ...}; phase_min/max = -1 if no chronological relations found
	# names = {obj_id: name, ...}
	# circulars = [obj_id, ...]
	
	errors = []
	
	if circulars:
		errors = ["Circular relations found between the following datings:"]
		for obj_id in circulars:
			errors.append("\t%s" % (names[obj_id]))
		return errors
	
	for obj_id in list(phasing.keys()):
		if phasing[obj_id] == [None, None]:
			del phasing[obj_id]
	
	phmax = 0
	for i in phasing:
		phmax = max(phmax, phasing[i][1])

	node_ids = sorted(list(phasing.keys()), key = lambda idx: phasing[idx][0])
	
	pyplot.figure(figsize = (12, 6))
	y = 0
	for obj_id in node_ids:
		if (not detailed) and ("," in names[obj_id]):
			continue
		x0, x1 = phasing[obj_id]
		if x0 == x1:
			pyplot.plot([x0], [y], "o", color = "gray")
		else:
			pyplot.barh(y = y, width = x1 - x0, left = x0, height = 0.5, color = "lightgray")
		pyplot.text((x0 + x1) / 2, y, names[obj_id], horizontalalignment = "center", verticalalignment = "center")
		y += 1
	pyplot.xlim(-1, phmax + 1)
	pyplot.xticks(list(range(phmax + 1)), list(range(phmax + 2))[1:])
	pyplot.yticks([], [])
	pyplot.xlabel("Order")
	pyplot.tight_layout()
	pyplot.show()
	
	return errors
