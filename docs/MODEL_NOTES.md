# Model notes

## Farm-risk model
The bundled `models/multifactor_xgb.joblib` is the multi-factor XGBoost model used by the risk engine. It is blended with a transparent rule baseline so the result can be explained and the application still has sensible guardrails.

## Plant image analysis
AgriTech intentionally separates:

- **Broad visual triage:** works on all plant parts and looks for broad visual patterns such as yellowing, necrotic/dark tissue, rot-like appearance, water-stress appearance and physical/pest-like damage.
- **Leaf-specific classifier:** optional CropGuard ResNet50 ONNX model trained on PlantVillage. It is only invoked for leaf photos and only when the crop has useful classes in that model.

The broad triage is not presented as an exact disease diagnosis.

## Why this is important
The CropGuard model card states that the source dataset is controlled leaf photography and warns that real field photographs are a different distribution. It also says the model covers 38 classes across 14 crops and will otherwise force out-of-distribution images into those classes. V7 prevents that model from being blindly used on roots, flowers and unsupported crops.
