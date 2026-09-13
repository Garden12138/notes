class_name TownConfig
extends RefCounted

const DEFAULT_API_BASE_URL := "http://127.0.0.1:8000"


static func api_base_url() -> String:
	var configured := OS.get_environment("CYBER_TOWN_API_URL").strip_edges()
	if configured.is_empty():
		return DEFAULT_API_BASE_URL
	return configured.trim_suffix("/")

