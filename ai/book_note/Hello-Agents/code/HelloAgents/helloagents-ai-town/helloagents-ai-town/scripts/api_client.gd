class_name CyberTownAPIClient
extends Node

signal health_checked(online: bool, conversation_ready: bool, message: String)
signal chat_completed(success: bool, message: String)

var base_url := TownConfig.api_base_url()


func check_health() -> void:
	var request := _new_request()
	request.request_completed.connect(_on_health_completed.bind(request))
	var error := request.request("%s/healthz" % base_url)
	if error != OK:
		request.queue_free()
		health_checked.emit(false, false, "无法发起后端健康检查")


func send_chat(npc_name: String, message: String) -> void:
	var request := _new_request()
	request.request_completed.connect(_on_chat_completed.bind(request))
	var payload := JSON.stringify({
		"npc_name": npc_name,
		"player_id": "player",
		"message": message,
	})
	var error := request.request(
		"%s/chat" % base_url,
		["Content-Type: application/json"],
		HTTPClient.METHOD_POST,
		payload,
	)
	if error != OK:
		request.queue_free()
		chat_completed.emit(false, "无法发送对话请求")


func _new_request() -> HTTPRequest:
	var request := HTTPRequest.new()
	request.timeout = 20.0
	add_child(request)
	return request


func _on_health_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray,
	request: HTTPRequest,
) -> void:
	request.queue_free()
	if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
		health_checked.emit(false, false, "后端未连接")
		return
	var data = JSON.parse_string(body.get_string_from_utf8())
	if typeof(data) != TYPE_DICTIONARY:
		health_checked.emit(false, false, "后端健康响应格式错误")
		return
	var ready := bool(data.get("conversation_ready", false))
	var message := "后端已连接"
	if not ready:
		message += "，NPC 对话将在 15.2 接入"
	health_checked.emit(true, ready, message)


func _on_chat_completed(
	result: int,
	response_code: int,
	_headers: PackedStringArray,
	body: PackedByteArray,
	request: HTTPRequest,
) -> void:
	request.queue_free()
	var data = JSON.parse_string(body.get_string_from_utf8())
	if result != HTTPRequest.RESULT_SUCCESS:
		chat_completed.emit(false, "对话请求失败")
		return
	if response_code != 200:
		var detail := "对话服务暂不可用"
		if typeof(data) == TYPE_DICTIONARY:
			detail = str(data.get("detail", detail))
		chat_completed.emit(false, detail)
		return
	if typeof(data) != TYPE_DICTIONARY or not data.has("message"):
		chat_completed.emit(false, "对话响应格式错误")
		return
	chat_completed.emit(true, str(data["message"]))
