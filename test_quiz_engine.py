from quiz_engine import grade_explain_back, generate_mcq, check_mcq_answer

topic = "Linux file permissions (chmod)"

print("=== Gate 1: Explain-Back ===")
# Simulate a decent explanation
explanation = "chmod changes who can read, write, or execute a file. The numbers like 755 represent permissions for owner, group, and others - 7 means read+write+execute, 5 means read+execute only. It's used to control access to files and scripts."
result = grade_explain_back(topic, explanation)
print("Score:", result["score"])
print("Passed:", result["passed"])
print("Feedback:", result["feedback"])

if result["passed"]:
    print("\n=== Gate 2: MCQ ===")
    mcq = generate_mcq(topic)
    print("Question:", mcq["question"])
    for key, val in mcq["options"].items():
        print(f"  {key}. {val}")
    print("Correct answer:", mcq["correct_answer"])
    print("Explanation:", mcq["explanation"])

    # Simulate answering correctly
    is_correct = check_mcq_answer(mcq, mcq["correct_answer"])
    print("\nSimulated correct answer check:", is_correct)
else:
    print("\nGate 1 failed - Gate 2 would not unlock in real flow")
