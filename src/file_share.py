import os


def save_file(filename: str, data: bytes, size: int) -> int:
   
    if not filename or data is None or size < 0:
        print("[FILE] Invalid parameters for save_file")
        return -1

  
    directory = os.path.dirname(filename)
    if directory:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"[FILE] Failed to create directory {directory}: {e}")
            return -1

    try:
        with open(filename, "wb") as file:
            written = file.write(data[:size])
            if written != size:
                print(f"[FILE] Failed to write complete file: {filename}")
                return -1
    except Exception as e:
        print(f"[FILE] Failed to open or write file {filename}: {e}")
        return -1

    print(f"[FILE] Saved file: {filename}, size: {size} bytes")
    return 0


def read_file(filename: str):

    if not filename:
        print("[FILE] Invalid parameters for read_file")
        return None, -1

    if not os.path.exists(filename):
        print(f"[FILE] File not found: {filename}")
        return None, -1

    try:
        with open(filename, "rb") as file:
            data = file.read()
            size = len(data)
    except Exception as e:
        print(f"[FILE] Failed to read file {filename}: {e}")
        return None, -1

    print(f"[FILE] Read file: {filename}, size: {size} bytes")
    return data, size


def file_exists(filename: str) -> int:
    
    if not filename:
        return 0
    return 1 if os.path.isfile(filename) else 0


def get_file_size(filename: str) -> int:
   
    if not filename:
        return -1
    try:
        return os.stat(filename).st_size
    except:
        return -1
