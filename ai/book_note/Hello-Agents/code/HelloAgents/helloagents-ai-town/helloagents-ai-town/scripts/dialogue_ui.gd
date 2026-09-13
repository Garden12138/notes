class_name DialogueUI
extends CanvasLayer

signal message_submitted(npc_name: String, message: String)
signal closed

@onready var overlay: ColorRect = $Overlay
@onready var npc_name_label: Label = $Overlay/Panel/Margin/Content/NPCName
@onready var npc_title_label: Label = $Overlay/Panel/Margin/Content/NPCTitle
@onready var dialogue_text: RichTextLabel = $Overlay/Panel/Margin/Content/DialogueText
@onready var player_input: LineEdit = $Overlay/Panel/Margin/Content/PlayerInput
@onready var send_button: Button = $Overlay/Panel/Margin/Content/Actions/SendButton
@onready var close_button: Button = $Overlay/Panel/Margin/Content/Actions/CloseButton

var current_npc_name := ""
var conversation_ready := false


func _ready() -> void:
	overlay.visible = false
	send_button.pressed.connect(_submit)
	close_button.pressed.connect(close)
	player_input.text_submitted.connect(_on_text_submitted)


func show_npc(_npc_id: String, npc_name: String, npc_title: String, ready: bool) -> void:
	current_npc_name = npc_name
	conversation_ready = ready
	npc_name_label.text = npc_name
	npc_title_label.text = npc_title
	dialogue_text.text = (
		"可以开始对话。" if ready else "后端已连接，但 NPC 对话服务尚未就绪。"
	)
	player_input.clear()
	_set_input_enabled(ready)
	overlay.visible = true
	if ready:
		player_input.grab_focus()
	else:
		close_button.grab_focus()


func show_response(success: bool, message: String) -> void:
	dialogue_text.text = message
	_set_input_enabled(conversation_ready)
	if success:
		player_input.clear()
		player_input.grab_focus()


func close() -> void:
	if not overlay.visible:
		return
	overlay.visible = false
	closed.emit()


func _submit() -> void:
	var message := player_input.text.strip_edges()
	if not conversation_ready or message.is_empty():
		return
	_set_input_enabled(false)
	dialogue_text.text = "正在等待 NPC 回复……"
	message_submitted.emit(current_npc_name, message)


func _set_input_enabled(enabled: bool) -> void:
	player_input.editable = enabled
	send_button.disabled = not enabled


func _on_text_submitted(_value: String) -> void:
	_submit()


func _unhandled_key_input(event: InputEvent) -> void:
	if (
		overlay.visible
		and event is InputEventKey
		and event.pressed
		and not event.echo
		and event.keycode == KEY_ESCAPE
	):
		close()
		get_viewport().set_input_as_handled()
