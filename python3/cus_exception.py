import sys
 
def custom_excepthook(exc_type, exc_value, exc_traceback):
    print(f"Unhandled exception: {exc_value}")
 
sys.excepthook = custom_excepthook
 
def risky_operation():
    raise ValueError("This is a test exception")
 
if __name__ == "__main__":
    risky_operation()