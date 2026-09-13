class_name CyberTownAPIClient
extends Node

signal health_checked(online: bool, conversation_ready: bool, message: String)
signal chat_response_received(npc_name: String, message: String)
signal chat_error(npc_name: String, error_message: String)
signal npc_status_received(dialogues: Dictionary)
signal npc_status_error(error_message: String)
signal npc_list_received(npcs: Array)
signal npc_list_error(error_message: String)

var http_health: HTTPRequest
var http_chat: HTTPRequest
var http_status: HTTPRequest
var http_npcs: HTTPRequest
var pending_chat_npc_name := ""


func _ready() -> void:
	http_health = _create_request(_on_health_request_completed)
	http_chat = _create_request(_on_chat_request_completed)
	http_status = _create_request(_on_status_request_completed)
	http_npcs = _create_request(_on_npcs_request_completed)


func check_health() -> void:
	if not _is_idle(http_health):
		return
	var error := http_health.request(Config.API_HEALTH)
	if error != OK:
		health_checked.emit(false, false, "无法发起后端健康检查")


func send_chat(npc_name: String, message: String, player_id := "player") -> void:
	var normalized_npc := npc_name.strip_edges()
	var normalized_message := message.strip_edges()
	if normalized_npc.is_empty() or normalized_message.is_empty():
		chat_error.emit(normalized_npc, "NPC 名称和消息不能为空")
		return
	if not _is_idle(http_chat):
		chat_error.emit(normalized_npc, "上一条对话仍在处理中")
		return

	pending_chat_npc_name = normalized_npc
	var payload := JSON.stringify({
		"npc_name": normalized_npc,
		"player_id": player_id.strip_edges(),
		"message": normalized_message,
	})
	var error := http_chat.request(
		Config.API_CHAT,
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		payload,
	)
	if error != OK:
		pending_chat_npc_name = ""
		chat_error.emit(normalized_npc, "无法发送对话请求：%s" % error)


func get_npc_status() -> void:
	if not _is_idle(http_status):
		return
	var error := http_status.request(Config.API_NPC_STATUS)
	if error != OK:
		npc_status_error.emit("无法获取 NPC 状态：%s" % error)


func get_npc_list() -> void:
	if not _is_idle(http_npcs):
		return
	var error := http_npcs.request(Config.API_NPCS)
	if error != OK:
		npc_list_error.emit("无法获取 NPC 列表：%s" % error)


func _create_request(callback: Callable) -> HTTPRequest:
	var request := HTTPRequest.new()
	request.timeout = Config.REQUEST_TIMEOUT
	add_child(request)
	request.request_completed.connect(callback)
	return request


func _is_idle(request: HTTPRequest) -> bool:
	return request.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED


func _parse_object(body: PackedByteArray) -> Dictionary:
	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) == TYPE_DICTIONARY:
		return parsed
	return {}


func _error_detail(data: Dictionary, fallback: String) -> String:
	if not data.has("detail"):
		return fallback
	var detail = data["detail"]
	if typeof(detail) == TYPE_STRING:
		return str(detail)
	return JSON.stringify(detail)


func _on_health_request_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray,
) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		health_checked.emit(false, false, "后端未连接")
		return
	var data := _parse_object(body)
	if response_code != 200:
		health_checked.emit(
			false,
			false,
			_error_detail(data, "健康检查失败：HTTP %s" % response_code),
		)
		return
	if data.is_empty():
		health_checked.emit(false, false, "后端健康响应格式错误")
		return
	var ready := bool(data.get("conversation_ready", false))
	var message := "后端已连接"
	if not ready:
		message += "，%s" % str(data.get("detail", "NPC 对话服务尚未就绪"))
	health_checked.emit(true, ready, message)


func _on_chat_request_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray,
) -> void:
	var requested_npc := pending_chat_npc_name
	pending_chat_npc_name = ""
	if result != HTTPRequest.RESULT_SUCCESS:
		chat_error.emit(requested_npc, "对话请求失败")
		return

	var data := _parse_object(body)
	if response_code != 200:
		chat_error.emit(
			requested_npc,
			_error_detail(data, "对话服务错误：HTTP %s" % response_code),
		)
		return
	if data.is_empty() or not bool(data.get("success", false)):
		chat_error.emit(requested_npc, "对话响应格式错误")
		return

	var response_npc := str(data.get("npc_name", "")).strip_edges()
	var response_message := str(data.get("message", "")).strip_edges()
	if response_npc != requested_npc or response_message.is_empty():
		chat_error.emit(requested_npc, "对话响应与当前请求不匹配")
		return
	chat_response_received.emit(response_npc, response_message)


func _on_status_request_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray,
) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		npc_status_error.emit("NPC 状态请求失败")
		return
	var data := _parse_object(body)
	if response_code != 200:
		npc_status_error.emit(
			_error_detail(data, "NPC 状态服务错误：HTTP %s" % response_code),
		)
		return
	var raw_dialogues = data.get("dialogues")
	if typeof(raw_dialogues) != TYPE_DICTIONARY:
		npc_status_error.emit("NPC 状态响应缺少 dialogues")
		return
	var dialogues: Dictionary = {}
	for npc_name in raw_dialogues:
		var dialogue = raw_dialogues[npc_name]
		if typeof(npc_name) == TYPE_STRING and typeof(dialogue) == TYPE_STRING:
			dialogues[str(npc_name)] = str(dialogue)
	npc_status_received.emit(dialogues)


func _on_npcs_request_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray,
) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		npc_list_error.emit("NPC 列表请求失败")
		return
	var data := _parse_object(body)
	if response_code != 200:
		npc_list_error.emit(
			_error_detail(data, "NPC 列表服务错误：HTTP %s" % response_code),
		)
		return
	var npcs = data.get("npcs")
	if typeof(npcs) != TYPE_ARRAY:
		npc_list_error.emit("NPC 列表响应缺少 npcs")
		return
	npc_list_received.emit(npcs)
