class_name TownPlayer
extends CharacterBody2D

@export var speed := 220.0


func _physics_process(_delta: float) -> void:
	var direction := Vector2.ZERO
	if Input.is_key_pressed(KEY_A):
		direction.x -= 1.0
	if Input.is_key_pressed(KEY_D):
		direction.x += 1.0
	if Input.is_key_pressed(KEY_W):
		direction.y -= 1.0
	if Input.is_key_pressed(KEY_S):
		direction.y += 1.0

	velocity = direction.normalized() * speed
	move_and_slide()
	position.x = clampf(position.x, 24.0, 936.0)
	position.y = clampf(position.y, 90.0, 516.0)

