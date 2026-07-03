class_name EventSystem
extends RefCounted


const EVENT_FILES := {
	"random": "res://data/events_random.json",
	"academic": "res://data/events_academic.json",
}

var events_by_type := {}


func _init() -> void:
	for event_type in EVENT_FILES.keys():
		var data := JsonLoader.load_dictionary(EVENT_FILES[event_type])
		events_by_type[event_type] = JsonLoader.get_array(data, "events").duplicate(true)


func get_random_event(event_type: String = "random") -> Dictionary:
	var events: Array = events_by_type.get(event_type, [])
	if events.is_empty():
		return {}
	return events.pick_random()


func apply_event(player: Player, event: Dictionary) -> Array[String]:
	if event.is_empty():
		return ["没有可用事件。"]

	var lines: Array[String] = [
		"【%s】" % str(event.get("title", "事件")),
		str(event.get("description", "")),
	]
	var effect: Dictionary = event.get("effect", {})
	var effect_lines := player.apply_effect(effect)
	if effect_lines.is_empty():
		lines.append("没有明显变化。")
	else:
		lines.append_array(effect_lines)
	return lines
