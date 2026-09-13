class_name TownNPC
extends CharacterBody2D

@export var npc_id := "npc"
@export var npc_name := "NPC"
@export var npc_title := "小镇居民"
@export var sprite_frames: SpriteFrames = null
@export var move_speed: float = 50.0
@export var wander_enabled := true
@export var wander_range: float = 90.0
@export var wander_interval_min: float = 3.0
@export var wander_interval_max: float = 8.0
@export var movement_bounds := Rect2(52.0, 102.0, 856.0, 392.0)

@onready var animated_sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var interaction_area: Area2D = $InteractionArea
@onready var name_label: Label = $NameLabel
@onready var role_label: Label = $RoleLabel
@onready var dialogue_label: Label = $DialogueLabel
@onready var prompt_label: Label = $InteractionPrompt

var player: TownPlayer = null
var spawn_position := Vector2.ZERO
var wander_target := Vector2.ZERO
var wander_timer := 0.0
var is_wandering := false
var is_interacting := false
var current_dialogue := ""
var dialogue_revision := 0


func _ready() -> void:
	add_to_group("npcs")
	name_label.text = npc_name
	role_label.text = npc_title
	dialogue_label.visible = false
	prompt_label.visible = false
	if sprite_frames != null:
		animated_sprite.sprite_frames = sprite_frames
	_play_animation("idle")
	interaction_area.body_entered.connect(_on_body_entered)
	interaction_area.body_exited.connect(_on_body_exited)
	spawn_position = global_position
	if wander_enabled:
		_choose_new_wander_target()
		_reset_wander_timer()


func _physics_process(delta: float) -> void:
	if is_interacting or not wander_enabled:
		_stop_wandering()
		return

	wander_timer -= delta
	if wander_timer <= 0.0:
		_choose_new_wander_target()
		_reset_wander_timer()

	if not is_wandering:
		_stop_wandering()
		return

	if global_position.distance_to(wander_target) < 8.0:
		is_wandering = false
		_stop_wandering()
		return

	var direction := global_position.direction_to(wander_target)
	velocity = direction * move_speed
	move_and_slide()
	_update_animation(direction)
	if get_slide_collision_count() > 0:
		is_wandering = false
		wander_timer = minf(wander_timer, 0.5)


func set_interacting(interacting: bool) -> void:
	is_interacting = interacting
	if interacting:
		_stop_wandering()


func update_dialogue(dialogue: String, duration: float = 10.0) -> void:
	current_dialogue = dialogue.strip_edges()
	dialogue_revision += 1
	var revision := dialogue_revision
	if current_dialogue.is_empty():
		dialogue_label.visible = false
		return
	dialogue_label.text = current_dialogue
	dialogue_label.visible = true
	await get_tree().create_timer(duration).timeout
	if revision == dialogue_revision:
		dialogue_label.visible = false


func _on_body_entered(body: Node2D) -> void:
	if body is TownPlayer:
		player = body as TownPlayer
		player.set_nearby_npc(self)
		prompt_label.visible = true


func _on_body_exited(body: Node2D) -> void:
	if body == player:
		player.set_nearby_npc(null)
		player = null
		prompt_label.visible = false


func _choose_new_wander_target() -> void:
	var offset := Vector2(
		randf_range(-wander_range, wander_range),
		randf_range(-wander_range, wander_range),
	)
	wander_target = spawn_position + offset
	wander_target.x = clampf(
		wander_target.x,
		movement_bounds.position.x,
		movement_bounds.end.x,
	)
	wander_target.y = clampf(
		wander_target.y,
		movement_bounds.position.y,
		movement_bounds.end.y,
	)
	is_wandering = true


func _reset_wander_timer() -> void:
	wander_timer = randf_range(wander_interval_min, wander_interval_max)


func _stop_wandering() -> void:
	velocity = Vector2.ZERO
	move_and_slide()
	_play_animation("idle")


func _update_animation(direction: Vector2) -> void:
	if absf(direction.x) > absf(direction.y):
		if direction.x > 0.0:
			_play_animation("walk_right", "walk", false)
		else:
			_play_animation("walk_left", "walk", true)
	elif direction.y > 0.0:
		_play_animation("walk_down", "walk")
	else:
		_play_animation("walk_up", "walk")


func _play_animation(
	preferred: StringName,
	fallback: StringName = &"idle",
	flip_h := false,
) -> void:
	if animated_sprite.sprite_frames == null:
		return
	animated_sprite.flip_h = flip_h
	if animated_sprite.sprite_frames.has_animation(preferred):
		animated_sprite.play(preferred)
	elif animated_sprite.sprite_frames.has_animation(fallback):
		animated_sprite.play(fallback)
