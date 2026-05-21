from urllib.parse import unquote


def display_filename(value: str) -> str:
    decoded = unquote(value).replace("\\", "/").split("/")[-1].strip()
    return decoded or value
