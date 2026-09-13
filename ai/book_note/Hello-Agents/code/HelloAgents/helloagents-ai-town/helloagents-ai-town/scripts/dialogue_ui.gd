class_name DialogueUI
extends CanvasLayer

signal message_submitted(npc_name: String, message: String)
signal closed

@onready var overlay: ColorRect = $Overlay
@onready var title_label: Label = $Overlay/Panel/Margin/Content/Title
@onready var status_label: Label = $Overlay/Panel/Margin/Content/Status
@onready var reply_label: RichTextLabel = $Overlay/Panel/Margin/Content/Reply
@onready var message_edit: LineEdit = $Overlay/Panel/Margin/Content/Message
@onready var send_button: Button = $Overlay/Panel/Margin/Content/Actions/Send
@onready var close_button: Button = $Overlay/Panel/Margin/Content/Actions/Close

var current_npc_name := ""
var conversation_ready := false


func _ready() -> void:
	overlay.visible = false
	send_button.pressed.connect(_submit)
	close_button.pressed.connect(close)
	message_edit.text_submitted.connect(_on_text_submitted)


func show_npc(_npc_id: String, display_name: String, role: String, ready: bool) -> void:
	current_npc_name = display_name
	conversation_ready = ready
	title_label.text = "%s · %s" % [display_name, role]
	status_label.text = "对话服务已就绪" if ready else "15.1 架构基线：对话服务尚未接入"
	reply_label.text = "你已进入 NPC 的交互范围。\n后续章节会在这里展示带记忆和好感度影响的回复。"
	message_edit.clear()
	message_edit.editable = ready
	send_button.disabled = not ready
	overlay.visible = true
	if ready:
		message_edit.grab_focus()
	else:
		close_button.grab_focus()


func show_response(success: bool, message: String) -> void:
	reply_label.text = message
	send_button.disabled = not conversation_ready
	if success:
		message_edit.clear()
		message_edit.grab_focus()


func close() -> void:
	if not overlay.visible:
		return
	overlay.visible = false
	closed.emit()


func _submit() -> void:
	var message := message_edit.text.strip_edges()
	if not conversation_ready or message.is_empty():
		return
	send_button.disabled = true
	reply_label.text = "正在等待 NPC 回复……"
	message_submitted.emit(current_npc_name, message)


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
