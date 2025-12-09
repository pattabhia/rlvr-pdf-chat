# test_with_lora.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mistral-7B-Instruct-v0.2",
    torch_dtype=torch.float16,
    device_map="auto"
)

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")

print("Loading LoRA adapter WITHOUT merging...")
model = PeftModel.from_pretrained(
    base_model,
    "/workspace/taj-model"
)

# Check if adapter is active
print(f"Active adapters: {model.active_adapters}")
print(f"Adapter loaded: {hasattr(model, 'peft_config')}")

model.eval()

def ask_taj(question):
    prompt = f"You are an assistant answering questions about Taj Hotels.\n\nQuestion: {question}\n\nAnswer:"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=80,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return text.split("Answer:")[-1].strip()

print("\n" + "="*70)
print("TESTING WITH LORA (NOT MERGED)")
print("="*70 + "\n")

answer = ask_taj("How much does a night at Taj Mahal Palace, Mumbai typically cost?")
print(f"Answer: {answer}\n")

if "24,000" in answer or "24000" in answer or "₹24" in answer:
    print("✅ LORA IS WORKING!")
else:
    print("❌ LORA NOT APPLYING")
    print("Expected: ₹24,000 - ₹65,000")