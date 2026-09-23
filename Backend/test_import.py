import sys
import traceback

with open("test_result.txt", "w", encoding="utf-8") as f:
    try:
        import main
        f.write("IMPORT OK\n")
    except Exception as e:
        f.write(f"ERROR: {e}\n")
        f.write(traceback.format_exc())
