class_name Player
extends RefCounted


var player_name := "研究生"
var year := 1
var semester := "上学期"
var week := 1
var action_points := 3
var max_action_points := 3
var sanity := 100
var int_stat := 50
var sen := 50
var edu := 50
var str_stat := 50
var soc := 50
var reputation := 0
var research_progress := 0
var research_unlocked := false
var courses_selected := false


func _init(name: String = "研究生") -> void:
	player_name = name


func change_sanity(delta: int) -> void:
	sanity = clampi(sanity + delta, 0, 100)


func apply_effect(effect: Dictionary) -> Array[String]:
	var lines: Array[String] = []
	if effect.has("sanity"):
		var delta := int(effect["sanity"])
		change_sanity(delta)
		lines.append("理智%+d" % delta)

	for key in ["INT", "SEN", "EDU", "STR", "SOC"]:
		if not effect.has(key):
			continue
		var delta := int(effect[key])
		match key:
			"INT":
				int_stat += delta
			"SEN":
				sen += delta
			"EDU":
				edu += delta
			"STR":
				str_stat += delta
			"SOC":
				soc += delta
		lines.append("%s%+d" % [key, delta])

	if effect.has("reputation"):
		var delta := int(effect["reputation"])
		reputation += delta
		lines.append("声望%+d" % delta)

	if effect.has("progress"):
		var delta := int(effect["progress"])
		research_progress = clampi(research_progress + delta, 0, 255)
		lines.append("灵感%+d" % delta)

	return lines


func status_lines() -> Array[String]:
	return [
		"%s  研%d %s 第%d周" % [player_name, year, semester, week],
		"理智: %d | 行动点: %d/%d" % [sanity, action_points, max_action_points],
		"INT: %d | SEN: %d | EDU: %d | STR: %d | SOC: %d" % [int_stat, sen, edu, str_stat, soc],
		"声望: %d | 灵感: %d | 科研: %s" % [reputation, research_progress, "已解锁" if research_unlocked else "未解锁"],
	]
