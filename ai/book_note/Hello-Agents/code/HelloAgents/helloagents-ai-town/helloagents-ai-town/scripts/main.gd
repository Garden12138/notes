extends Node2D

@onready var api_client: CyberTownAPIClient = $APIClient
@onready var player: TownPlayer = $Player
@onready var dialogue_ui: DialogueUI = $DialogueUI
@onready var backend_status: Label = $HUD/BackendStatus

var conversation_ready := false
var current_npc: TownNPC = null


func _ready() -> void:
	player.interaction_requested.connect(_on_interaction_requested)
	api_client.health_checked.connect(_on_health_checked)
	api_client.chat_completed.connect(_on_chat_completed)
	dialogue_ui.message_submitted.connect(api_client.send_chat)
	dialogue_ui.closed.connect(_on_dialogue_closed)
	api_client.check_health()


func _on_health_checked(online: bool, ready: bool, message: String) -> void:
	conversation_ready = online and ready
	backend_status.text = message
	backend_status.modulate = Color("7ad7ae") if online else Color("f08d74")


func _on_interaction_requested(npc: Node) -> void:
	if not (npc is TownNPC):
		return
	current_npc = npc as TownNPC
	player.set_interacting(true)
	current_npc.set_interacting(true)
	dialogue_ui.show_npc(
		current_npc.npc_id,
		current_npc.npc_name,
		current_npc.npc_title,
		conversation_ready,
	)


func _on_chat_completed(success: bool, message: String) -> void:
	dialogue_ui.show_response(success, message)
	if success and is_instance_valid(current_npc):
		current_npc.update_dialogue(message)


func _on_dialogue_closed() -> void:
	player.set_interacting(false)
	if is_instance_valid(current_npc):
		current_npc.set_interacting(false)
	current_npc = null
