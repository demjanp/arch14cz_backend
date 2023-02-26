from arch14cz_backend.utils.fnc_convert import (float_or_none)

import numpy as np
from scipy.interpolate import interp1d

def load_calibration_curve(fcalib, interpolate = False):
	# load calibration curve
	# data from: fcalib 14c file
	# returns: [[CalBP, ConvBP, CalSigma], ...], sorted by CalBP
	
	with open(fcalib, "r", encoding="latin1") as f:
		data = f.read()
	data = data.split("\n")
	cal_curve = []
	for line in data:
		line = line.strip()
		if not line:
			continue
		if line.startswith("#"):
			continue
		cal_curve.append([np.float64(value) for value in line.split(",")])
	cal_curve = np.array(cal_curve, dtype = np.float64)
	cal_curve = cal_curve[np.argsort(cal_curve[:,0])]
	
	if interpolate:
		cal_bp = np.arange(cal_curve[:,0].min(), cal_curve[:,0].max() + 1, 1)
		cal_curve = np.vstack((
			cal_bp,
			interp1d(cal_curve[:,0], cal_curve[:,1], kind = "quadratic")(cal_bp),
			interp1d(cal_curve[:,0], cal_curve[:,2], kind = "linear")(cal_bp),
		)).T
	
	return cal_curve.astype(np.float64)

def calibrate(age, uncert, curve_conv_age, curve_uncert):
	# calibrate a 14C measurement
	# calibration formula as defined by Bronk Ramsey 2008, doi: 10.1111/j.1475-4754.2008.00394.x
	# age: uncalibrated 14C age BP
	# uncert: 1 sigma uncertainty
	
	sigma_sum = uncert**2 + curve_uncert**2
	return (np.exp(-(age - curve_conv_age)**2 / (2 * sigma_sum)) / np.sqrt(sigma_sum))

def calc_range(cal_age, distribution, p = 0.9545, p_threshold = 0.0001, max_multiplier = 32):
	
	def _find_rng(values, weights, v_min, v_max, mul):
		
		vs = np.linspace(values.min(), values.max(), values.shape[0] * mul)
		weights = np.interp(vs, values, weights)
		values = vs
		weights /= weights.sum()
		idx_start = max(0, int(np.where(values <= v_min)[0].max()) - 1)
		idx_end = min(values.shape[0] - 1, int(np.where(values >= v_max)[0].min()) + 1)
		values = values[idx_start:idx_end]
		weights = weights[idx_start:idx_end]
		levels = np.unique(weights)
		levels.sort()
		lvl_prev = 0
		for lvl in levels[::-1]:
			mask = (weights >= lvl)
			p_sum = weights[mask].sum()
			if p_sum >= p:
				mask = (weights >= lvl_prev)
				p_sum = weights[mask].sum()
				idxs = np.where(mask)[0]
				return values[idxs.min()], values[idxs.max()], p - p_sum
			lvl_prev = lvl
		idxs = np.where(weights > 0)[0]
		return values[idxs.min()], values[idxs.max()], 1 - p	
	
	v_min, v_max = cal_age.min(), cal_age.max()
	p_diff_opt = np.inf
	v_opt = [v_min, v_max]
	mul = 2
	while True:
		v_min, v_max, p_diff = _find_rng(cal_age, distribution, v_min, v_max, mul)
		if p_diff >= p_diff_opt:
			mul *= 2
		if p_diff < p_diff_opt:
			p_diff_opt = p_diff
			v_opt = [v_min, v_max]
		if p_diff <= p_threshold:
			break
		if mul > max_multiplier:
			break
	
	return v_opt

def calc_mean(cal_age, distribution):
	
	return (cal_age * (distribution / distribution.sum())).sum()

def calc_mean_std(cal_age, distribution):
	# returns weighted mean and standard deviation of cal_age
	
	dist = distribution / distribution.sum()
	mean = (cal_age * dist).sum()
	std = np.sqrt((((cal_age - mean)**2) * dist).sum())
	return mean, std

def update_ranges(cmodel, path_curve, progress = None, cnt = 1, cmax = None):
	
	curve = load_calibration_curve(path_curve, interpolate = False)
	cls_c14 = cmodel.get_class("C_14_Analysis")
	if cls_c14 is None:
		return ["C_14_Analysis Class not found"], 0
	objs = cls_c14.get_members(direct_only = True)
	if cmax is None:
		cmax = len(objs)
	for obj in objs:
		if (progress is not None) and (cmax is not None):
			progress.update_state(value = cnt, maximum = cmax)
			if progress.cancel_pressed():
				return ["Cancelled by user"], cnt
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
	
	return [], cnt
