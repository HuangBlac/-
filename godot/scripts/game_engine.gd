class_name GameEngine
extends RefCounted


enum Phase {
	COURSE_SELECTING,
	COURSE_ATTENDING,
	RESEARCH_UNLOCKED,
}

var player: Player
var course_system: CourseSystem
var event_system: EventSystem
var phase := Phase.COURSE_SELECTING
var message_log: Array[String] = []


func _init(player_name: String = "研究生") -> void:
	player = Player.new(player_name)
	course_system = CourseSystem.new()
	event_system = EventSystem.new()
	message_log = [
		"欢迎来到克苏鲁研究院。",
		"你将在论文、导师邮件和不可名状的低语之间寻找毕业路线。",
		"第一步：选择 3 门选修课。",
	]


func get_status_text() -> String:
	return "\n".join(player.status_lines())


func get_log_text() -> String:
	return "\n\n".join(message_log)


func get_actions() -> Array[Dictionary]:
	match phase:
		Phase.COURSE_SELECTING:
			var actions: Array[Dictionary] = []
			var electives := course_system.get_available_electives()
			for index in range(electives.size()):
				var course: Dictionary = electives[index]
				actions.append({
					"id": "select_%d" % index,
					"label": "%d. %s" % [index + 1, str(course.get("name", "未命名课程"))],
					"description": str(course.get("description", "")),
				})
			actions.append({
				"id": "confirm_courses",
				"label": "确认选课",
				"description": "选择 3 门后进入上课阶段。",
			})
			return actions
		Phase.COURSE_ATTENDING:
			return [
				{"id": "attend_class", "label": "上课", "description": "参加课程学习，可能提升属性。"},
				{"id": "trigger_event", "label": "看看今天发生了什么", "description": "触发一个日常事件。"},
				{"id": "rest", "label": "休息", "description": "恢复少量理智并推进一周。"},
			]
		Phase.RESEARCH_UNLOCKED:
			return [
				{"id": "read_literature", "label": "阅读文献", "description": "用学术事件积累灵感。"},
				{"id": "trigger_event", "label": "看看今天发生了什么", "description": "触发一个日常事件。"},
				{"id": "rest", "label": "休息", "description": "恢复少量理智并推进一周。"},
			]
	return []


var _pending_course_indexes: Array[int] = []


func do_action(action_id: String) -> void:
	message_log.clear()

	if action_id.begins_with("select_"):
		_toggle_course_selection(action_id)
		return

	match action_id:
		"confirm_courses":
			_confirm_courses()
		"attend_class":
			_consume_action()
			message_log.append_array(course_system.attend_class(player))
			_after_action()
		"trigger_event":
			_consume_action()
			message_log.append_array(event_system.apply_event(player, event_system.get_random_event("random")))
			_after_action()
		"read_literature":
			_consume_action()
			message_log.append_array(event_system.apply_event(player, event_system.get_random_event("academic")))
			_after_action()
		"rest":
			player.change_sanity(5)
			message_log.append("你睡了一个相对完整的觉。理智+5")
			_advance_week()
		_:
			message_log.append("这个行动还没有实现。")


func _toggle_course_selection(action_id: String) -> void:
	var index := int(action_id.trim_prefix("select_"))
	if _pending_course_indexes.has(index):
		_pending_course_indexes.erase(index)
		message_log.append("已取消选择第 %d 门课。" % [index + 1])
	elif _pending_course_indexes.size() >= 3:
		message_log.append("已经选择 3 门课，先确认或取消一门。")
	else:
		_pending_course_indexes.append(index)
		message_log.append("已选择第 %d 门课。" % [index + 1])

	if not _pending_course_indexes.is_empty():
		message_log.append("当前选择：%s" % _format_selected_courses())


func _confirm_courses() -> void:
	var result := course_system.select_electives(_pending_course_indexes, player)
	message_log.append_array(result)
	if player.courses_selected:
		phase = Phase.COURSE_ATTENDING
		_pending_course_indexes.clear()
		message_log.append("接下来开始上课。")


func _format_selected_courses() -> String:
	var names: Array[String] = []
	var electives := course_system.get_available_electives()
	for index in _pending_course_indexes:
		if index >= 0 and index < electives.size():
			names.append(str(electives[index].get("name", "未命名课程")))
	return "、".join(names)


func _consume_action() -> void:
	player.action_points = max(0, player.action_points - 1)


func _after_action() -> void:
	if phase == Phase.COURSE_ATTENDING and player.week >= 4:
		phase = Phase.RESEARCH_UNLOCKED
		player.research_unlocked = true
		message_log.append("课程阶段告一段落。科研入口已经解锁。")

	if player.action_points <= 0:
		_advance_week()


func _advance_week() -> void:
	player.week += 1
	player.action_points = player.max_action_points
	message_log.append("时间推进到第 %d 周。" % player.week)
