from pathlib import Path
import shutil
from huggingface_hub import hf_hub_download

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "models"
MODELS.mkdir(parents=True, exist_ok=True)
REPO = "AbhiCommits/cropguard-models"

print("AgriTech: downloading optional leaf-specific CropGuard fp32 model (~95 MB)...")
print("This model is used only for supported LEAF scans.")
model_src = hf_hub_download(repo_id=REPO, filename="cropguard.onnx")
model_dst = MODELS / "cropguard.onnx"
shutil.copy2(model_src, model_dst)
print(f"Leaf model installed: {model_dst} ({model_dst.stat().st_size / 1024 / 1024:.1f} MB)")
print("Class labels are already bundled with AgriTech V7.")
