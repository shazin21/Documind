
from sentence_transformers import SentenceTransformer

# Load a small model that converts text into numerical vectors
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

chunks = [
    "Employees can request annual leave.",
    "The vehicle requires regular engine maintenance.",
    "Annual leave requests require manager approval."
]

# Convert each text chunk into an embedding
vectors = model.encode(
    chunks,
    normalize_embeddings=True
)

print("Number of chunks:", len(chunks))
print("Embedding shape:", vectors.shape)

# Convert the user's question into an embedding
question = "Who approves leave requests?"

query_vector = model.encode(
    [question],
    normalize_embeddings=True
)[0]

# Compare the question against every chunk
scores = vectors @ query_vector

# Print the most relevant chunk first
for index in scores.argsort()[::-1]:
    print(
        round(float(scores[index]), 3),
        chunks[index]
    )
