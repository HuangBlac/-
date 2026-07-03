class_name CourseSystem
extends RefCounted


const COURSE_DATA_PATH := "res://data/courses.json"

var required_courses: Array = []
var elective_courses: Array = []
var selected_electives: Array = []


func _init() -> void:
	var data := JsonLoader.load_dictionary(COURSE_DATA_PATH)
	required_courses = JsonLoader.get_array(data, "required_courses").duplicate(true)
	elective_courses = JsonLoader.get_array(data, "elective_courses").duplicate(true)


func get_available_electives() -> Array:
	return elective_courses


func select_electives(indexes: Array[int], player: Player) -> Array[String]:
	if indexes.size() != 3:
		return ["需要选择 3 门选修课。"]

	var selected: Array = []
	for index in indexes:
		if index < 0 or index >= elective_courses.size():
			return ["选课编号无效，请重新选择。"]
		selected.append(elective_courses[index])

	selected_electives = selected
	player.courses_selected = true

	var lines: Array[String] = ["选课完成："]
	for course in selected_electives:
		lines.append("- %s" % str(course.get("name", "未命名课程")))
	return lines


func attend_class(player: Player) -> Array[String]:
	var active_courses := get_active_courses()
	if active_courses.is_empty():
		player.research_unlocked = true
		return ["本学期课程已经完成。你可以开始尝试科研路线。"]

	var course: Dictionary = active_courses.pick_random()
	var attrs: Dictionary = course.get("attributes", {})
	var lines: Array[String] = [
		"你认真学习了《%s》。" % str(course.get("name", "未命名课程")),
		str(course.get("description", "")),
	]

	var gained := false
	for key in attrs.keys():
		if randf() > 0.65:
			continue
		var gain := randi_range(1, 2)
		player.apply_effect({key: gain})
		lines.append("%s+%d" % [key, gain])
		gained = true

	if not gained:
		lines.append("你记下了很多笔记，但暂时还没有明显突破。")

	var sanity_loss := randi_range(1, 3)
	player.change_sanity(-sanity_loss)
	lines.append("理智-%d" % sanity_loss)
	return lines


func get_active_courses() -> Array:
	var active := required_courses.duplicate(true)
	active.append_array(selected_electives)
	return active
