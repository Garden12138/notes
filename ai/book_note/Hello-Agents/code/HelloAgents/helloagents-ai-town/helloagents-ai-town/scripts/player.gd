class_name TownPlayer
extends CharacterBody2D

signal interaction_requested(npc: Node)

@export var speed: float = 200.0
@export var movement_bounds := Rect2(52.0, 102.0, 856.0, 392.0)

@onready var animated_sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var camera: Camera2D = $Camera2D
@onready var direction_marker: Polygon2D = $Direction
@onready var interact_sound: AudioStreamPlayer = $InteractSound
@onready var running_sound: AudioStreamPlayer = $RunningSound

var nearby_npc: Node = null
var is_interacting := false
var is_playing_running_sound := false


func _ready() -> void:
	add_to_group("player")
	camera.enabled = true
	_play_animation("idle")


func _physics_process(_delta: float) -> void:
	if is_interacting:
		velocity = Vector2.ZERO
		move_and_slide()
		_play_animation("idle")
		_stop_running_sound()
		return

	var input_direction := _get_input_direction()
	velocity = input_direction * speed
	move_and_slide()
	global_position.x = clampf(
		global_position.x,
		movement_bounds.position.x,
		movement_bounds.end.x,
	)
	global_position.y = clampf(
		global_position.y,
		movement_bounds.position.y,
		movement_bounds.end.y,
	)
	_update_animation(input_direction)
	_update_running_sound(input_direction)


func _unhandled_key_input(event: InputEvent) -> void:
	if (
		not is_interacting
		and nearby_npc != null
		and event is InputEventKey
		and event.pressed
		and not event.echo
		and (event.keycode == KEY_E or event.keycode == KEY_ENTER)
	):
		if interact_sound.stream != null:
			interact_sound.play()
		interaction_requested.emit(nearby_npc)
		get_viewport().set_input_as_handled()


func set_nearby_npc(npc: Node) -> void:
	nearby_npc = npc


func set_interacting(interacting: bool) -> void:
	is_interacting = interacting
	if interacting:
		velocity = Vector2.ZERO
		_stop_running_sound()


func _get_input_direction() -> Vector2:
	var direction := Vector2.ZERO
	if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
		direction.x -= 1.0
	if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
		direction.x += 1.0
	if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
		direction.y -= 1.0
	if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
		direction.y += 1.0
	return direction.normalized()


func _update_animation(direction: Vector2) -> void:
	if direction.is_zero_approx():
		_play_animation("idle")
		return

	if absf(direction.x) > absf(direction.y):
		if direction.x > 0.0:
			_play_animation("walk_right", "walk", false)
			direction_marker.rotation = PI / 2.0
		else:
			_play_animation("walk_left", "walk", true)
			direction_marker.rotation = -PI / 2.0
	elif direction.y > 0.0:
		_play_animation("walk_down", "walk")
		direction_marker.rotation = PI
	else:
		_play_animation("walk_up", "walk")
		direction_marker.rotation = 0.0


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


func _update_running_sound(direction: Vector2) -> void:
	if running_sound.stream == null:
		return
	if not direction.is_zero_approx() and not is_playing_running_sound:
		running_sound.play()
		is_playing_running_sound = true
	elif direction.is_zero_approx():
		_stop_running_sound()


func _stop_running_sound() -> void:
	if is_playing_running_sound:
		running_sound.stop()
		is_playing_running_sound = false
