import subprocess
import sys

def find_apple_id(contact_name):
    applescript = f'''
    set contactName to "{contact_name}"
    
    tell application "Contacts"
        set theContact to first person whose name is contactName
        set appleID to value of email of theContact
        if appleID is missing value then
            return "未找到 Apple ID"
        else
            return appleID
        end if
    end tell
    '''
    
    # 调用 AppleScript 执行
    result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
    return result.stdout.strip()

def send_imessage(apple_id, message_content):
    applescript = f'''
    tell application "Messages"
        set targetService to 1st service whose service type = iMessage
        set targetBuddy to buddy "{apple_id}" of targetService
        send "{message_content}" to targetBuddy
    end tell
    '''
    
    # 调用 AppleScript 执行
    subprocess.run(["osascript", "-e", applescript])

def main():
    # 获取命令行传入的参数
    if len(sys.argv) != 3:
        print("Usage: python script.py <接收者名称> <发送内容>")
        sys.exit(1)
    
    contact_name = sys.argv[1]
    message_content = sys.argv[2]

    # 根据接收者名称找到 Apple ID
    apple_id = find_apple_id(contact_name)
    if apple_id == "未找到 Apple ID":
        print("错误: 没有找到该联系人对应的 Apple ID")
        sys.exit(1)

    print(f"找到 Apple ID: {apple_id}")

    # 发送消息
    send_imessage(apple_id, message_content)
    print(f"消息已发送给 {contact_name}: {message_content}")

if __name__ == "__main__":
    main()