import re
from pathlib import Path
from uuid import uuid4


def sanitize_filename(filename: str) -> str:
    """Strips path traversal sequences and unsafe characters from filenames."""
    # Extract only the base name without directory components
    clean_name = Path(filename).name
    # Keep only alphanumeric characters, dashes, underscores, and dots
    clean_name = re.sub(r"[^a-zA-Z0-9._-]", "_", clean_name)
    # Remove leading dots or dashes to avoid hidden or command-like files
    clean_name = clean_name.lstrip(".-")
    return clean_name or "document.pdf"


def generate_opaque_storage_name(extension: str = ".pdf") -> str:
    """Generates an unguessable opaque filename for safe server-side storage."""
    safe_ext = extension if extension.startswith(".") else f".{extension}"
    return f"{uuid4().hex}{safe_ext}"


def validate_pdf_bytes(content: bytes) -> tuple[bool, str]:
    """Validates that bytes represent a valid PDF file by inspecting magic headers."""
    if len(content) < 5:
        return False, "File is too small to be a valid PDF."
    # Check for standard PDF magic header (%PDF-)
    if not content.startswith(b"%PDF-"):
        # Some PDFs have leading whitespace or BOM; allow check within the first 1024 bytes
        if b"%PDF-" not in content[:1024]:
            return False, "File lacks valid PDF magic header (%PDF-)."
    return True, ""


def sanitize_for_prompt(text: str) -> str:
    """Neutralizes known prompt-injection tokens and system overrides inside retrieved passages."""
    if not text:
        return ""
    # Neutralize explicit markdown instruction blocks and common jailbreak headers
    sanitized = re.sub(r"(?i)<\s*(system|prompt|instruction)[^>]*>", "[instruction block removed]", text)
    sanitized = re.sub(r"(?i)</\s*(system|prompt|instruction)\s*>", "", sanitized)
    sanitized = re.sub(r"(?i)ignore\s+(all\s+)?previous\s+instructions", "[disregarded instruction]", sanitized)
    return sanitized
