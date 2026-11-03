# Third-party model attribution

AgriTech V7 can optionally download **CropGuard - Crop Disease Classifier (38 classes)** from:

https://huggingface.co/AbhiCommits/cropguard-models

The Hugging Face repository lists the model license as **CC-BY-SA-4.0**. The weights are not bundled in this ZIP; `SETUP_WINDOWS.bat`/`INSTALL_OR_REPAIR_LEAF_AI.bat` downloads the fp32 `cropguard.onnx` file from the model repository.

The model is trained on the PlantVillage dataset and is used only as an optional leaf-specific classifier. AgriTech's broad visual triage and farm-risk model are separate components.
