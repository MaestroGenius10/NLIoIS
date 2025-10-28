def extract_text_from_file(file_path: str) -> str:
    """Извлекает текст из TXT-файла, удаляя пустые строки."""
    if not file_path.lower().endswith(".txt"):
        raise ValueError("Поддерживается только формат .txt")

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # Оставляем только непустые строки
    non_empty_lines = [line.rstrip() for line in lines if line.strip()]
    return "\n".join(non_empty_lines)

