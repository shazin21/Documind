
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Creates a tool to divide large text into smaller pieces
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""]
)


def chunk_page(page_text: str) -> list[str]:
    return splitter.split_text(page_text)


if __name__ == "__main__":
    example_text = """
    Retrieval Augmented Generation, or RAG, helps AI systems
    answer questions using external information.

    First, the system retrieves relevant text. Then, a language
    model uses that text to generate a grounded answer.
    """

    chunks = chunk_page(example_text)

    for number, chunk in enumerate(chunks, start=1):
        print(f"\nChunk {number}:\n{chunk}")
