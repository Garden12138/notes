on run argv
	if (count of argv) < 2 then
		error "用法: osascript add_boss_reminder.scpt \"标题\" \"YYYY-MM-DD HH:MM\" [列表名] [备注]"
	end if
	
	set reminderTitle to item 1 of argv
	set reminderTimeText to item 2 of argv
	
	if (count of argv) ≥ 3 then
		set listName to item 3 of argv
	else
		set listName to "老板提醒"
	end if
	
	if (count of argv) ≥ 4 then
		set reminderNotes to item 4 of argv
	else
		set reminderNotes to ""
	end if
	
	set oldTID to AppleScript's text item delimiters
	set AppleScript's text item delimiters to {"-", " ", ":"}
	set parts to text items of reminderTimeText
	set AppleScript's text item delimiters to oldTID
	
	if (count of parts) is not 5 then
		error "时间格式错误，请使用 YYYY-MM-DD HH:MM，例如 2026-04-18 08:00"
	end if
	
	set y to (item 1 of parts) as integer
	set m to (item 2 of parts) as integer
	set d to (item 3 of parts) as integer
	set hh to (item 4 of parts) as integer
	set mm to (item 5 of parts) as integer
	
	set remindDate to current date
	set year of remindDate to y
	set month of remindDate to m
	set day of remindDate to d
	set hours of remindDate to hh
	set minutes of remindDate to mm
	set seconds of remindDate to 0
	
	tell application "Reminders"
		if not (exists list listName) then
			make new list with properties {name:listName}
		end if
		
		tell list listName
			set newReminder to make new reminder with properties {name:reminderTitle, body:reminderNotes, remind me date:remindDate}
		end tell
	end tell
	
	return "已创建提醒：" & reminderTitle & " @ " & reminderTimeText & " -> " & listName
end run
