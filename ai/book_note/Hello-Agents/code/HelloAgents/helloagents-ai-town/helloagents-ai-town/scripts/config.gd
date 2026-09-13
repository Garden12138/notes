extends Node

const DEFAULT_API_BASE_URL := "http://127.0.0.1:8000"
const NPC_STATUS_UPDATE_INTERVAL := 30.0
const REQUEST_TIMEOUT := 20.0

var API_BASE_URL := ""
var API_HEALTH := ""
var API_CHAT := ""
var API_NPC_STATUS := ""
var API_NPCS := ""


func _enter_tree() -> void:
	var configured := OS.get_environment("CYBER_TOWN_API_URL").strip_edges()
	configure_api_base_url(
		DEFAULT_API_BASE_URL if configured.is_empty() else configured,
	)


func configure_api_base_url(value: String) -> void:
	API_BASE_URL = value.strip_edges().trim_suffix("/")
	if API_BASE_URL.is_empty():
		API_BASE_URL = DEFAULT_API_BASE_URL
	API_HEALTH = "%s/healthz" % API_BASE_URL
	API_CHAT = "%s/chat" % API_BASE_URL
	API_NPC_STATUS = "%s/npcs/status" % API_BASE_URL
	API_NPCS = "%s/npcs" % API_BASE_URL

