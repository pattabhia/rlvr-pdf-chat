# test_model.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

print("Loading merged DPO model...")
model = AutoModelForCausalLM.from_pretrained(
    "/workspace/taj-merged",
    torch_dtype=torch.float16,
    device_map="auto"
)
tokenizer = AutoTokenizer.from_pretrained("/workspace/taj-merged")
model.eval()

print("✅ Model loaded!\n")

def ask_taj(question):
    prompt = f"You are an assistant answering questions about Taj Hotels.\n\nQuestion: {question}\n\nAnswer:"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return text.split("Answer:")[-1].strip()

# Test
print("="*70)
print("TESTING DPO FINE-TUNED MODEL")
print("="*70 + "\n")

questions = [
    "How much does a night at Taj Mahal Palace, Mumbai typically cost?",
    "What is the average price range for Taj Mahal Palace, Mumbai?",
    "How much does Taj Lake Palace Udaipur cost per night?",
]

for i, q in enumerate(questions, 1):
    answer = ask_taj(q)
    print(f"Q{i}: {q}")
    print(f"A{i}: {answer}")
    print("-"*70 + "\n")

print("\n✅ If you see ₹24,000-65,000 for Mumbai, YOUR DPO TRAINING WORKED!")