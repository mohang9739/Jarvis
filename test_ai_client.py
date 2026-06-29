from ai_client import ask_ai, ask_ai_json

print("=== Test 1: Plain text ===")
result = ask_ai("Say hello in exactly 5 words.")
print(result)

print("\n=== Test 2: JSON mode ===")
result = ask_ai_json("Return a JSON object with two fields: 'score' (a number 1-10) and 'feedback' (a short string), rating how clear this sentence is: 'A list is a mutable ordered collection in Python.'")
print(result)
print("Type:", type(result))
