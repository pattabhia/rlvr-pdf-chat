#!/usr/bin/env python3
"""
DPO Training Script

Train a custom customer support model using Direct Preference Optimization (DPO).

Requirements:
    pip install trl transformers datasets accelerate peft bitsandbytes torch

Usage:
    # Full fine-tuning (requires GPU with 24GB+ VRAM)
    python scripts/train_dpo.py \
        --dataset data/dpo_dataset/dpo_training_data.jsonl \
        --model meta-llama/Llama-3.2-3B-Instruct \
        --output ./trained_model
    
    # LoRA fine-tuning (works on 16GB GPU)
    python scripts/train_dpo.py \
        --dataset data/dpo_dataset/dpo_training_data.jsonl \
        --model meta-llama/Llama-3.2-3B-Instruct \
        --output ./trained_model \
        --use-lora \
        --lora-r 16 \
        --lora-alpha 32
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List

import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
)
from trl import DPOTrainer
from peft import LoraConfig, get_peft_model


def load_dpo_dataset(dataset_path: Path) -> Dataset:
    """Load DPO dataset from JSONL file."""
    data = []
    
    with open(dataset_path, 'r') as f:
        for line in f:
            entry = json.loads(line.strip())
            # Extract only the fields needed for DPO
            data.append({
                'prompt': entry['prompt'],
                'chosen': entry['chosen'],
                'rejected': entry['rejected']
            })
    
    print(f"Loaded {len(data)} DPO training pairs")
    return Dataset.from_list(data)


def format_prompt(example: Dict[str, str]) -> Dict[str, str]:
    """
    Format prompt for instruction-tuned models.
    
    Uses Llama 3.2 chat template format.
    """
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful customer support assistant. Answer questions based on the provided context.<|eot_id|><|start_header_id|>user<|end_header_id|>

{example['prompt']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    
    return {
        'prompt': prompt,
        'chosen': example['chosen'],
        'rejected': example['rejected']
    }


def main():
    parser = argparse.ArgumentParser(description='Train DPO model')
    parser.add_argument(
        '--dataset',
        type=Path,
        required=True,
        help='Path to DPO dataset (JSONL)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='meta-llama/Llama-3.2-3B-Instruct',
        help='Base model to fine-tune'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('./trained_model'),
        help='Output directory for trained model'
    )
    parser.add_argument(
        '--use-lora',
        action='store_true',
        help='Use LoRA for parameter-efficient fine-tuning'
    )
    parser.add_argument(
        '--lora-r',
        type=int,
        default=16,
        help='LoRA rank (default: 16)'
    )
    parser.add_argument(
        '--lora-alpha',
        type=int,
        default=32,
        help='LoRA alpha (default: 32)'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=3,
        help='Number of training epochs (default: 3)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=4,
        help='Training batch size (default: 4)'
    )
    parser.add_argument(
        '--learning-rate',
        type=float,
        default=5e-5,
        help='Learning rate (default: 5e-5)'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("DPO Training Configuration")
    print("="*60)
    print(f"Dataset: {args.dataset}")
    print(f"Base model: {args.model}")
    print(f"Output: {args.output}")
    print(f"Use LoRA: {args.use_lora}")
    if args.use_lora:
        print(f"  LoRA rank: {args.lora_r}")
        print(f"  LoRA alpha: {args.lora_alpha}")
    print(f"Epochs: {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"Learning rate: {args.learning_rate}")
    print("="*60)
    
    # Load dataset
    print("\n📂 Loading dataset...")
    dataset = load_dpo_dataset(args.dataset)
    
    # Format prompts
    print("📝 Formatting prompts...")
    dataset = dataset.map(format_prompt)
    
    # Split into train/eval (90/10)
    split_dataset = dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = split_dataset['train']
    eval_dataset = split_dataset['test']
    
    print(f"Train samples: {len(train_dataset)}")
    print(f"Eval samples: {len(eval_dataset)}")
    
    # Load model and tokenizer
    print(f"\n🤖 Loading model: {args.model}")
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )
    
    # Apply LoRA if requested
    if args.use_lora:
        print(f"🔧 Applying LoRA (r={args.lora_r}, alpha={args.lora_alpha})")
        peft_config = LoraConfig(
            r=args.lora_r,
            lora_alpha=args.lora_alpha,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]
        )
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        logging_steps=10,
        save_steps=100,
        eval_steps=100,
        evaluation_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=True,
        bf16=True,
        gradient_checkpointing=True,
        remove_unused_columns=False,
    )
    
    # Initialize DPO trainer
    print("\n🎯 Initializing DPO trainer...")
    trainer = DPOTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        beta=0.1,  # DPO temperature parameter
        max_length=512,
        max_prompt_length=256,
    )
    
    # Train
    print("\n🚀 Starting training...")
    trainer.train()
    
    # Save final model
    print(f"\n💾 Saving model to {args.output}")
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    
    print("\n✅ Training complete!")
    print(f"Model saved to: {args.output}")
    print("\nNext steps:")
    print("1. Test the model locally")
    print("2. Deploy to AWS SageMaker or HuggingFace")
    print("3. Update RLVR system to use the new model")


if __name__ == "__main__":
    main()

