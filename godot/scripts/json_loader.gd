class_name JsonLoader
extends RefCounted


static func load_dictionary(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_warning("JSON file not found: %s" % path)
		return {}

	var text := FileAccess.get_file_as_string(path)
	var parsed = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("JSON file is not a dictionary: %s" % path)
		return {}
	return parsed


static func get_array(data: Dictionary, key: String) -> Array:
	var value = data.get(key, [])
	if typeof(value) == TYPE_ARRAY:
		return value
	return []
