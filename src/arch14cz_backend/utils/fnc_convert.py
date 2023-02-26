from deposit.utils.fnc_serialize import (try_numeric)

def float_or_none(value):
	
	value = try_numeric(value)
	if not (isinstance(value, int) or isinstance(value, float)):
		return None
	return float(value)

def int_or_none(value):
	
	value = float_or_none(value)
	if value is None:
		return value
	return int(value)

def str_or_empty(value):
	
	if value is None:
		return ""
	return str(value)
