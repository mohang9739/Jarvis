from meal_handler import handle_meal

print("=== Test 1: CHOICE scenario (should allow pushback) ===")
result = handle_meal("I'm thinking of eating biryani for lunch")
print("Is constraint:", result["is_constraint"])
print("Response:", result["response"])
print("Estimated calories:", result["calories"])

print("\n=== Test 2: CONSTRAINT scenario (should adapt, not argue) ===")
result = handle_meal("I only have biryani available right now, nothing else")
print("Is constraint:", result["is_constraint"])
print("Response:", result["response"])
print("Estimated calories:", result["calories"])

print("\n=== Test 3: Symptom-aware scenario ===")
from health_engine import supabase
supabase.table("symptom_log").insert({"symptom": "stomach issues", "active": True}).execute()
result = handle_meal("family made chicken curry and rice, what should I eat")
print("Response:", result["response"])

# cleanup test symptom
supabase.table("symptom_log").update({"active": False}).eq("symptom", "stomach issues").execute()
