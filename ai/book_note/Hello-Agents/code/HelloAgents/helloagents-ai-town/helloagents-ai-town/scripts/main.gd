extends Node2D

@onready var api_client: CyberTownAPIClient = APIClient
@onready var player: TownPlayer = $Player
@onready var dialogue_ui: DialogueUI = $DialogueUI
@onready var backend_status: Label = $HUD/BackendStatus
@onready var npc_container: Node2D = $NPCs

var conversation_ready := false
var current_npc: TownNPC = null
var status_update_timer := 0.0
var npc_nodes: Dictionary = {}
var npc_catalog: Array = []


func _ready() -> void:
	for node in npc_container.get_children():
		if node is TownNPC:
			var npc := node as TownNPC
			npc_nodes[npc.npc_name] = npc

	player.interaction_requested.connect(_on_interaction_requested)
	dialogue_ui.message_submitted.connect(_on_message_submitted)
	dialogue_ui.closed.connect(_on_dialogue_closed)
	api_client.health_checked.connect(_on_health_checked)
	api_client.chat_response_received.connect(_on_chat_response_received)
	api_client.chat_error.connect(_on_chat_error)
	api_client.npc_status_received.connect(_on_npc_status_received)
	api_client.npc_status_error.connect(_on_npc_status_error)
	api_client.npc_list_received.connect(_on_npc_list_received)
	api_client.npc_list_error.connect(_on_npc_list_error)

	api_client.check_health()
	api_client.get_npc_status()
	api_client.get_npc_list()


func _process(delta: float) -> void:
	status_update_timer += delta
	if status_update_timer >= Config.NPC_STATUS_UPDATE_INTERVAL:
		status_update_timer = 0.0
		api_client.get_npc_status()


func _on_health_checked(online: bool, ready: bool, message: String) -> void:
	conversation_ready = online and ready
	backend_status.text = message
	backend_status.modulate = Color("7ad7ae") if online else Color("f08d74")
	dialogue_ui.set_connection_state(conversation_ready, message)


func _on_message_submitted(npc_name: String, message: String) -> void:
	api_client.send_chat(npc_name, message)


func _on_interaction_requested(npc: Node) -> void:
	if not (npc is TownNPC):
		return
	current_npc = npc as TownNPC
	player.set_interacting(true)
	current_npc.set_interacting(true)
	dialogue_ui.start_dialogue(
		current_npc.npc_id,
		current_npc.npc_name,
		current_npc.npc_title,
		conversation_ready,
	)


func _on_chat_response_received(npc_name: String, message: String) -> void:
	dialogue_ui.on_chat_response_received(npc_name, message)
	var npc := get_npc_node(npc_name)
	if npc != null:
		npc.update_dialogue(message)


func _on_chat_error(npc_name: String, error_message: String) -> void:
	dialogue_ui.on_chat_error(npc_name, error_message)


func _on_npc_status_received(dialogues: Dictionary) -> void:
	for npc_name in dialogues:
		var npc := get_npc_node(str(npc_name))
		if npc == null or npc == current_npc:
			continue
		npc.update_dialogue(str(dialogues[npc_name]))


func _on_npc_status_error(error_message: String) -> void:
	print("[WARN] ", error_message)


func _on_npc_list_received(npcs: Array) -> void:
	npc_catalog = npcs.duplicate(true)


func _on_npc_list_error(error_message: String) -> void:
	print("[WARN] ", error_message)


func get_npc_node(npc_name: String) -> TownNPC:
	var node = npc_nodes.get(npc_name)
	if node is TownNPC:
		return node as TownNPC
	return null


func _on_dialogue_closed() -> void:
	player.set_interacting(false)
	if is_instance_valid(current_npc):
		current_npc.set_interacting(false)
	current_npc = null
