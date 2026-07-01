def build_document_text(chunk: dict, topics: list[str]) -> str:
    return (
        f"Act: {chunk['act_name']}\n"
        f"Category: {chunk['category']}\n"
        f"Section: {chunk['section_number']}\n"
        f"Title: {chunk['section_title']}\n"
        f"Topics: {', '.join(topics) if topics else 'general'}\n\n"
        f"{chunk['text']}"
    )