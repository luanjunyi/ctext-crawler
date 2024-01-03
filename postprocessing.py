DOUBLE_SPACE_CHINESE = "　　"


def postprocess(text: str) -> str:
    text = text.strip()
    if not text.startswith(DOUBLE_SPACE_CHINESE):
        text = DOUBLE_SPACE_CHINESE + text
    return text
