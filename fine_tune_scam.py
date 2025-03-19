import os
import torch
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments, EarlyStoppingCallback
from datasets import load_dataset
import evaluate

# 1️⃣ Load your CSV dataset (Make sure 'Scamdetection.csv' is in your working directory).
dataset = load_dataset('csv', data_files={'data': 'Scamdetection.csv'}, delimiter=',')

# 2️⃣ Split dataset into train & test (Use 10% for validation).
dataset = dataset['data'].train_test_split(test_size=0.1)

# 3️⃣ Load the tokenizer and **pre-finetuned model** instead of starting from scratch.
model_path = "./finetuned_model"
tokenizer = BertTokenizer.from_pretrained(model_path)
model = BertForSequenceClassification.from_pretrained(model_path, num_labels=2)

# 4️⃣ Tokenize the dataset.
def tokenize_function(examples):
    return tokenizer(examples['text'], truncation=True, padding='max_length', max_length=128)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

# 5️⃣ Define the accuracy evaluation metric.
accuracy_metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = logits.argmax(axis=-1)
    return accuracy_metric.compute(predictions=predictions, references=labels)

# 6️⃣ Enable mixed precision (`fp16`) if GPU is available.
fp16_enabled = torch.cuda.is_available()

# 7️⃣ Optimized Training Arguments for Faster Training (~10-15 min).
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=1,  # Quick training for 1 epoch
    per_device_train_batch_size=16,  # Increase if GPU available
    per_device_eval_batch_size=16,
    evaluation_strategy="steps",  # Evaluate every N steps
    eval_steps=50,  # Evaluate every 50 steps
    logging_steps=10,
    learning_rate=2e-5,  # Optimized learning rate
    fp16=fp16_enabled,  # Enable fp16 if using GPU
    save_steps=50,  # Save model every 50 steps
    load_best_model_at_end=True,
)

# 8️⃣ Initialize Trainer with Early Stopping.
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
    compute_metrics=compute_metrics,
    callbacks=[EarlyStoppingCallback(early_stopping_patience=1)],  # Stop early if no improvement
)

# 9️⃣ Fine-tune the model (Resume training on pre-finetuned model).
trainer.train()

# 🔟 Save the further fine-tuned model.
model.save_pretrained("./finetuned_model_v2")  # Saving new version
tokenizer.save_pretrained("./finetuned_model_v2")

print("✅ Fine-tuning completed and saved to './finetuned_model_v2'.")
