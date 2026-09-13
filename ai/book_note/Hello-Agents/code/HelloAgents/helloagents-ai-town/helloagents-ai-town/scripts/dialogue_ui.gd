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
var request_pending := false


func _ready() -> void:
	overlay.visible = false
	send_button.pressed.connect(_submit)
	close_button.pressed.connect(close)
	player_input.text_submitted.connect(_on_text_submitted)


func start_dialogue(
	_npc_id: String,
	npc_name: String,
	npc_title: String,
	ready: bool,
) -> void:
	current_npc_name = npc_name
	conversation_ready = ready
	npc_name_label.text = npc_name
	npc_title_label.text = npc_title
	dialogue_text.clear()
	dialogue_text.append_text("[color=gray]与 %s 的对话开始……[/color]\n" % npc_name)
	if not ready:
		dialogue_text.add_text("NPC 对话服务尚未就绪。\n")
	player_input.clear()
	_set_controls_enabled(ready and not request_pending)
	overlay.visible = true
	if ready and not request_pending:
		player_input.grab_focus()
	else:
		close_button.grab_focus()


func set_connection_state(ready: bool, message: String) -> void:
	conversation_ready = ready
	if overlay.visible and not request_pending:
		_set_controls_enabled(ready)
		if not ready:
			dialogue_text.add_text("%s\n" % message)


func on_chat_response_received(npc_name: String, response: String) -> void:
	request_pending = false
	close_button.disabled = false
	if npc_name != current_npc_name or not overlay.visible:
		return
	dialogue_text.append_text("[color=yellow]%s：[/color] " % npc_name)
	dialogue_text.add_text(response)
	dialogue_text.add_text("\n")
	_set_controls_enabled(conversation_ready)
	if conversation_ready:
		player_input.grab_focus()


func on_chat_error(npc_name: String, error_message: String) -> void:
	request_pending = false
	close_button.disabled = false
	if npc_name != current_npc_name or not overlay.visible:
		return
	dialogue_text.append_text("[color=red]请求失败：[/color] ")
	dialogue_text.add_text(error_message)
	dialogue_text.add_text("\n")
	_set_controls_enabled(conversation_ready)
	if conversation_ready:
		player_input.grab_focus()


func close() -> void:
	if not overlay.visible or request_pending:
		return
	overlay.visible = false
	current_npc_name = ""
	closed.emit()


func _submit() -> void:
	var message := player_input.text.strip_edges()
	if (
		not conversation_ready
		or request_pending
		or current_npc_name.is_empty()
		or message.is_empty()
	):
		return
	dialogue_text.append_text("[color=cyan]玩家：[/color] ")
	dialogue_text.add_text(message)
	dialogue_text.add_text("\n")
	player_input.clear()
	request_pending = true
	_set_controls_enabled(false)
	close_button.disabled = true
	message_submitted.emit(current_npc_name, message)


func _set_controls_enabled(enabled: bool) -> void:
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
