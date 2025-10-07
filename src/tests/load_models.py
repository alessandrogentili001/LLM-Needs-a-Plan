from transformers import AutoModelForCausalLM, AutoTokenizer

print("--- Starting Model Loading ---")

# Llama 4
print("\n1. Loading Llama 4 model...")
llama_path = "src/models/Llama-4-Scout-17B-16E-Instruct"
print(f"   - Path: {llama_path}")
try:
    llama_tokenizer = AutoTokenizer.from_pretrained(llama_path)
    print("   - Llama tokenizer loaded successfully.")
    llama_model = AutoModelForCausalLM.from_pretrained(llama_path)
    print("   - Llama model loaded successfully.")
    print("✅ Llama 4 loading complete.")
except Exception as e:
    print(f"❌ Error loading Llama 4: {e}")


# Phi 4
print("\n2. Loading Phi 4 model...")
phi_path = "src/models/Phi4"
print(f"   - Path: {phi_path}")
try:
    phi_tokenizer = AutoTokenizer.from_pretrained(phi_path)
    print("   - Phi tokenizer loaded successfully.")
    phi_model = AutoModelForCausalLM.from_pretrained(phi_path)
    print("   - Phi model loaded successfully.")
    print("✅ Phi 4 loading complete.")
except Exception as e:
    print(f"❌ Error loading Phi 4: {e}")

print("\n--- Model Loading Finished ---")

