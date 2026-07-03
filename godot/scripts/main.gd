extends Control


@onready var name_panel: PanelContainer = %NamePanel
@onready var name_input: LineEdit = %NameInput
@onready var start_button: Button = %StartButton
@onready var status_label: Label = %StatusLabel
@onready var log_label: RichTextLabel = %LogLabel
@onready var actions_box: VBoxContainer = %ActionsBox

var engine: GameEngine


func _ready() -> void:
	start_button.pressed.connect(_on_start_pressed)
	name_input.text_submitted.connect(func(_text: String) -> void: _on_start_pressed())
	_set_game_visible(false)


func _on_start_pressed() -> void:
	var player_name := name_input.text.strip_edges()
	if player_name.is_empty():
		player_name = "研究生"
	engine = GameEngine.new(player_name)
	name_panel.visible = false
	_set_game_visible(true)
	_refresh()


func _set_game_visible(is_visible: bool) -> void:
	status_label.visible = is_visible
	log_label.visible = is_visible
	actions_box.visible = is_visible


func _refresh() -> void:
	status_label.text = engine.get_status_text()
	log_label.text = engine.get_log_text()
	_rebuild_actions()


func _rebuild_actions() -> void:
	for child in actions_box.get_children():
		child.queue_free()

	for action in engine.get_actions():
		var button := Button.new()
		var label := str(action.get("label", "行动"))
		var description := str(action.get("description", ""))
		button.text = label if description.is_empty() else "%s\n%s" % [label, description]
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		button.custom_minimum_size = Vector2(0, 56)
		button.pressed.connect(_on_action_pressed.bind(str(action.get("id", ""))))
		actions_box.add_child(button)


func _on_action_pressed(action_id: String) -> void:
	if engine == null:
		return
	engine.do_action(action_id)
	_refresh()
