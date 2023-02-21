import numpy as np
import networkx as nx

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
		else:
			general.add(name)
	for name in general:
		if name not in obj_lookup:
			obj_lookup[name] = cmodel.add_object_with_descriptors(cls, {"Name": name})
	for name in detailed:
		name_general = to_general(name)
		obj_lookup[name_general].add_relation(obj_lookup[name], "contains")

def get_phasing(cmodel, dating_cls = "Relative_Dating", name_descr = "Name", before_rel = "before", same_as_rel = "same_as", contains_rel = "contains"):
	# cmodel = Deposit GUI DCModel
	# returns phasing, names, circulars
	# 	phasing = {obj_id: [phase_min, phase_max], ...}; phase_min/max = None if no chronological relations found
	# 	names = {obj_id: name, ...}
	#	circulars = [obj_id, ...]
	
	def extract_datings(cmodel, dating_cls, name_descr, before_rel, contains_rel):
		# returns G = nx.DiGraph
		# G.nodes[obj_id]["name"] = dating name
		# G.edges() = [(obj_id1, obj_id2), ...]; obj_id1 -> before -> obj_id2
		
		G = nx.DiGraph()
		
		cls = cmodel.get_class(dating_cls)
		if cls is None:
			return G
		
		for obj in cls.get_members(direct_only = True):
			G.add_node(obj.id, name = obj.get_descriptor(name_descr))
		for obj1 in cls.get_members(direct_only = True):
			objs1 = set([obj1.id])
			for obj, rel in obj1.get_relations():
				if rel != contains_rel:
					continue
				objs1.add(obj.id)
			objs2 = set()
			for obj2, rel in obj1.get_relations():
				if rel != before_rel:
					continue
				objs2.add(obj2.id)
				for obj, rel in obj2.get_relations():
					if rel != contains_rel:
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
	
	G = extract_datings(cmodel, dating_cls, name_descr, before_rel, contains_rel)
	
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

