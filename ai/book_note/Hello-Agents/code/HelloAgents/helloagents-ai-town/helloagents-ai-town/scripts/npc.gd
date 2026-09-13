class_name TownNPC
extends Area2D

signal interaction_requested(npc_id: String, display_name: String, role: String)

@export var npc_id := "npc"
@export var display_name := "NPC"
@export var role := "小镇居民"

@onready var name_label: Label = $NameLabel
@onready var role_label: Label = $RoleLabel
@onready var prompt: Label = $Prompt

var player_nearby := false


func _ready() -> void:
	add_to_group("npcs")
	name_label.text = display_name
	role_label.text = role
	prompt.visible = false
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)


func _unhandled_key_input(event: InputEvent) -> void:
	if (
		player_nearby
		and event is InputEventKey
		and event.pressed
		and not event.echo
		and event.keycode == KEY_E
	):
		interaction_requested.emit(npc_id, display_name, role)
		get_viewport().set_input_as_handled()


func _on_body_entered(body: Node2D) -> void:
	if body is TownPlayer:
		player_nearby = true
		prompt.visible = true


func _on_body_exited(body: Node2D) -> void:
	if body is TownPlayer:
		player_nearby = false
		prompt.visible = false

