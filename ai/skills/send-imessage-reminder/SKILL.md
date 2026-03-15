---
name: send-imessage-reminder
description: Send iMessage reminders to a specific contact. This skill allows you to send messages either immediately or at a scheduled time, based on the contact's name and the message content.
---

## Prerequisites
- Ensure you have Python installed on your system.
- Ensure the AppleScript component (`osascript`) is functional on macOS to interact with the Messages app.
- OpenClaw must be installed and configured to create and trigger custom skills.

## Skill Functions

### 1. Find Apple ID from Contact Name
This skill retrieves the Apple ID of a contact based on the given **contact name**. It accesses the macOS Contacts app to find the corresponding Apple ID associated with the contact.

### 2. Send iMessage
Once the Apple ID is retrieved, the skill sends the specified message content via iMessage to the identified contact.

### 3. Trigger Time (Optional)
You can specify a **trigger time** to send the message at a particular time. If no trigger time is specified, the message is sent immediately.

## Skill Input Parameters

- **contact_name**: The name of the contact to whom the iMessage will be sent. (e.g., "John Doe")
- **message_content**: The content of the message to be sent. (e.g., "This is a reminder message.")
- **trigger_time** (optional): The time at which to send the message. The format is `YYYY-MM-DD HH:MM:SS`. If not provided, the message is sent immediately.

### Example Input

```json
{
  "contact_name": "曾佳达",
  "message_content": "这是一个提醒消息",
  "trigger_time": "2026-02-06 10:00:00"
}

## Quick Start

### Sending Immediate Message
To send an immediate message to a contact via iMessage, run the following command:
```bash
python3 script/send-imessage.py **contact_name** **message_content**