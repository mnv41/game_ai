import torch

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Number of GPUs available: {torch.cuda.device_count()}")

if not torch.cuda.is_available():
    print("WARNING: CUDA is not available. Running on CPU will be SLOW.")
    print(
        "Please ensure you have CUDA installed correctly and that PyTorch is built with CUDA support."
    )
else:
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")  # Print GPU name
