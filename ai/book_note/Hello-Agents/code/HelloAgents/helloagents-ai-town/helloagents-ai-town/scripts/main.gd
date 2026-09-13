extends Node2D

@onready var api_client: CyberTownAPIClient = $APIClient
@onready var player: TownPlayer = $Player
@onready var dialogue_ui: DialogueUI = $DialogueUI
@onready var backend_status: Label = $HUD/BackendStatus

var conversation_ready := false


func _ready() -> void:
	for node in get_tree().get_nodes_in_group("npcs"):
		if node is TownNPC:
			node.interaction_requested.connect(_on_interaction_requested)
	api_client.health_checked.connect(_on_health_checked)
	api_client.chat_completed.connect(dialogue_ui.show_response)
	dialogue_ui.message_submitted.connect(api_client.send_chat)
	dialogue_ui.closed.connect(_on_dialogue_closed)
	api_client.check_health()


func _on_health_checked(online: bool, ready: bool, message: String) -> void:
	conversation_ready = online and ready
	backend_status.text = message
	backend_status.modulate = Color("7ad7ae") if online else Color("f08d74")


func _on_interaction_requested(
	npc_id: String,
	display_name: String,
	role: String,
) -> void:
	player.velocity = Vector2.ZERO
	player.set_physics_process(false)
	dialogue_ui.show_npc(npc_id, display_name, role, conversation_ready)


func _on_dialogue_closed() -> void:
	player.set_physics_process(true)
