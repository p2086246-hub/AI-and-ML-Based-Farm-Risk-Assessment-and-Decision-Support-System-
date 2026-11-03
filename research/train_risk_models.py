from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from xgboost import XGBClassifier

ROOT=Path(__file__).resolve().parents[1]
MODEL_DIR=ROOT/"models"; MODEL_DIR.mkdir(exist_ok=True)
DATA_DIR=ROOT/"research"/"data"; DATA_DIR.mkdir(exist_ok=True)
rng=np.random.default_rng(42)
N=8000

temp=rng.uniform(18,44,N); hum=rng.uniform(25,98,N); rain=np.clip(rng.gamma(1.4,8,N),0,90)
soil=rng.uniform(8,45,N); disease=np.clip(rng.beta(2,3,N)*100,0,100); et0=rng.uniform(1,9,N); stage=rng.integers(0,4,N)
weather=np.clip(15+np.maximum(0,temp-30)*5+np.maximum(0,hum-85)*1.2+np.maximum(0,rain-35)*1.2,0,100)
water=np.clip(12+np.maximum(0,24-soil)*3+np.maximum(0,temp-30)*3+np.maximum(0,et0-4)*3.5-np.minimum(rain,20)*1.3,0,100)
crop=np.clip(.30*weather+.35*water+.30*disease+np.where(stage>=2,8,2),0,100)
risk=np.clip(.25*weather+.30*water+.25*disease+.20*crop+rng.normal(0,5,N),0,100)
y=np.where(risk>=70,2,np.where(risk>=40,1,0))
# small noise prevents a perfect synthetic benchmark
flip=rng.random(N)<0.05
y[flip]=rng.integers(0,3,flip.sum())

df=pd.DataFrame({"temperature_c":temp,"humidity_pct":hum,"rainfall_24h_mm":rain,"soil_moisture_pct":soil,"disease_probability_pct":disease,"et0_mm":et0,"crop_stage_code":stage,"risk_score_rule":risk,"risk_class":y})
df.to_csv(DATA_DIR/"synthetic_farm_risk_benchmark.csv",index=False)
train,test=train_test_split(df,test_size=.2,random_state=42,stratify=df.risk_class)
features=["temperature_c","humidity_pct","rainfall_24h_mm","soil_moisture_pct","disease_probability_pct","et0_mm","crop_stage_code"]
subsets={"weather_only":["temperature_c","humidity_pct","rainfall_24h_mm","et0_mm"],"weather_crop":["temperature_c","humidity_pct","rainfall_24h_mm","et0_mm","crop_stage_code"],"weather_crop_soil":["temperature_c","humidity_pct","rainfall_24h_mm","soil_moisture_pct","et0_mm","crop_stage_code"],"all_factors":features}
metrics={}
for name,cols in subsets.items():
    model=XGBClassifier(n_estimators=180,max_depth=4,learning_rate=.07,subsample=.9,colsample_bytree=.9,objective="multi:softprob",num_class=3,random_state=42,n_jobs=2)
    model.fit(train[cols],train.risk_class)
    pred=model.predict(test[cols])
    metrics[name]={"features":cols,"accuracy":round(accuracy_score(test.risk_class,pred),4),"weighted_f1":round(f1_score(test.risk_class,pred,average="weighted"),4)}
    if name=="all_factors":
        joblib.dump(model,MODEL_DIR/"multifactor_xgb.joblib")
        imp={c:round(float(v),4) for c,v in zip(cols,model.feature_importances_)}
        (MODEL_DIR/"feature_importance.json").write_text(json.dumps(imp,indent=2))
(MODEL_DIR/"metrics.json").write_text(json.dumps({"dataset":"synthetic academic benchmark","rows":N,"random_seed":42,"metrics":metrics},indent=2))
print(json.dumps(metrics,indent=2))
