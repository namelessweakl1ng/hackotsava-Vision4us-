import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
import json

# --- Parameters ---
BATCH_SIZE = 8
EPOCHS = 10
IMG_SIZE = 224
DATA_DIR = "dataset"
MODEL_PATH = "art_model.pth"
LABELS_PATH = "labels.json"

# --- Data transforms ---
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# --- Dataset ---
train_data = datasets.ImageFolder(DATA_DIR, transform=transform)
train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)

# --- Labels ---
labels = train_data.classes
with open(LABELS_PATH, "w") as f:
    json.dump(labels, f)
print("✅ Labels saved:", labels)

# --- Model ---
model = models.resnet18(pretrained=True)
for param in model.parameters():
    param.requires_grad = False  # freeze backbone

num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, len(labels))  # replace classifier

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# --- Training setup ---
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.fc.parameters(), lr=0.001)

# --- Train loop ---
for epoch in range(EPOCHS):
    running_loss = 0.0
    correct = 0
    total = 0
    for inputs, targets in train_loader:
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()

    print(f"Epoch [{epoch+1}/{EPOCHS}] | Loss: {running_loss/len(train_loader):.3f} | Acc: {100*correct/total:.2f}%")

# --- Save model ---
torch.save(model.state_dict(), MODEL_PATH)
print(f"✅ Model saved as {MODEL_PATH}")
