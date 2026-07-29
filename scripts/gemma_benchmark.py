from ollama import Client
import time

client = Client(host="http://localhost:11434")

start = time.perf_counter()

response = client.chat(
    model="gemma3:4b",
    messages=[
        {
            "role": "user",
            "content": "Reply with exactly one word: AnalystGPT",
        }
    ],
    options={
        "temperature": 0,
        "num_predict": 10,
    },
)

print("Time:", time.perf_counter() - start)
print(response.message.content)