# AgriTech V7 — Smart Farm Intelligence

AgriTech is a farmer-first college web application that combines farm details, live weather, plant-photo analysis and a bundled XGBoost model to produce explainable farm-risk decisions.

## V7 highlights

- New AgriTech visual identity and logo across login, sidebar, header and browser tab.
- Mobile-number + password registration/login; OTP is used only for Forgot Password.
- Free-text crop name: the farmer is not restricted to a fixed crop list.
- Crop-aware stage suggestions plus generic stages for other crops.
- Expanded irrigation methods and irrigation-water sources.
- Easy location search with suggestions, exact coordinates, automatic weather preview, Google Map preview, OpenStreetMap backup and GPS capture.
- Full weather centre: temperature, feels-like temperature, humidity, rain, wind, pressure, cloud cover, UV, visibility, modeled soil moisture, sunrise/sunset and 7-day forecast.
- Real browser camera capture plus separate gallery upload.
- Plant-part selection: leaf, flower, fruit/pod, stem, root, whole plant, seed/grain or other.
- Broad visual plant-health triage for all plant parts, plus an optional leaf-specific ONNX disease model for supported leaf cases.
- Photo risk score, confidence and image-quality checks.
- Detailed treatment explanation: problem, visible symptoms, possible causes, non-chemical actions, prevention, chemical/pesticide category where justified, reason for that category, when NOT to spray and safety/registration reminder.
- Disease Progress Tracker compares the latest scan with a previous scan of the same crop + plant part.
- Farm Risk Engine: bundled XGBoost + transparent rules, individual risk factors, prediction confidence and prioritized actions.
- Weather-aware spray window and smart irrigation timing.
- What-if Risk Simulator.
- **What Changed?** comparison between the newest and previous farm assessments.
- **Smart Action Calendar** with today/future tasks and completion tracking.
- Assessment history now shows **date + time**, farm, risk, confidence and source, with 7/30-day filters.
- English, Hindi, Marathi and Gujarati UI with voice playback for recommendations.

> Academic prototype: risk, image and treatment outputs are decision-support signals, not a substitute for field diagnosis, product labels or a qualified agriculture professional.

---

## First time on a Windows PC

1. Extract this ZIP into a completely new folder.
2. Do not copy `.venv`, `node_modules`, database files or source files from older versions.
3. Make sure Python 3.11/3.12 and Node.js LTS are installed.
4. Double-click:

```text
START_HERE_FIRST_TIME.bat
```

The setup will:

1. create the Python virtual environment,
2. install backend dependencies,
3. run the backend/AI self-test,
4. attempt to download and verify the optional leaf-specific ONNX model,
5. install frontend packages,
6. run a frontend production build as a syntax/build test,
7. then launch the project.

When setup succeeds you will see `SETUP COMPLETE`.

### Every later run

Double-click:

```text
RUN_PROJECT.bat
```

Keep both terminal windows open and visit:

```text
http://localhost:5173
```

Backend Swagger/API documentation:

```text
http://127.0.0.1:8000/docs
```

Optional health check after setup:

```text
VERIFY_PROJECT.bat
```

This reruns the backend AI self-test and a frontend production build.

---

## Recommended first demo flow

1. Register using Name + Mobile Number + Password.
2. Open **Farm**.
3. Type a village/city/location and select one suggestion, or use current GPS.
4. Confirm the exact coordinates, automatic weather preview and map.
5. Enter any crop name, sowing date, stage, soil, irrigation and water source; save the farm.
6. Open **Plant Health**, select crop + plant part, then use **Camera** or **Gallery**.
7. Analyze the photo and review risk, confidence, problem explanation and detailed treatment guidance.
8. Take another comparable scan later to demonstrate **Disease Progress**.
9. Open **Dashboard**, use live weather and run the Farm Risk Assessment.
10. Review overall risk, factor risks, confidence, explanations, priority actions, spray window, irrigation timing and What-if simulation.
11. Open **Action Plan** and complete a generated farm task.
12. Run at least two assessments, then open **History** to demonstrate date/time, graph, filters and **What Changed?**.

---

## Location and Google Map behavior

The Farm page is designed so the location is resolved before saving:

- Start typing a village/city/district.
- Select one of the suggestions. This stores exact latitude/longitude and automatically loads the weather preview.
- Or use **Current Location** and allow browser location permission.
- The preview defaults to a Google Maps embed.
- If Google embed is blocked on the current browser/network, click **Backup Map** for OpenStreetMap.
- **Open in Google Maps** always opens the selected coordinates directly in Google Maps.

Live location search, map tiles and live weather require internet access.

---

## Camera

The **Camera** button uses the browser `getUserMedia()` API; it does not use the gallery input. Allow camera permission when Chrome asks. On mobile the app requests the environment/rear camera when available.

If camera access is blocked: Chrome → site settings for `localhost` → Camera → Allow → refresh.

---

## Plant AI and pesticide guidance

AgriTech deliberately separates two capabilities:

1. **Broad plant-part visual triage** — runs locally for leaf/flower/fruit/stem/root/whole-plant/seed images and produces image quality, stress/risk signals and general guidance.
2. **Optional leaf-specific disease classifier** — used only when the uploaded case is appropriate for that model. It is not blindly applied to roots, flowers or unsupported cases.

Treatment guidance avoids inventing a pesticide brand or dose. When chemical intervention is justified, it provides a treatment **category/active-ingredient class**, why it may be relevant, non-chemical steps, and conditions when spraying should be avoided. The farmer must verify the current crop-use registration and product label.

If the optional leaf model did not install during setup, run:

```text
INSTALL_OR_REPAIR_LEAF_AI.bat
```

Broad plant-health analysis and the main farm-risk model still work without that optional download.

---

## Forgot Password OTP

OTP is used only for Forgot Password. The default local setting is:

```text
SMS_MODE=console
```

so the OTP is printed in the backend terminal for a college/local demo. Real SMS can be configured in `backend/.env` using Twilio credentials.

---

## Local data

V7 uses:

```text
backend/agritech_v7.db
```

To erase all local users, farms, scans, action tasks and assessments, run:

```text
RESET_DATABASE.bat
```

Do this only when you intentionally want a completely fresh database.

---

## Important limitations

- Weather and modeled soil moisture come from a weather service and can differ from on-farm sensors.
- Visual plant analysis cannot replace laboratory or expert diagnosis.
- Chemical advice is intentionally category-level and must be checked against the latest official registration/product label.
- Disease Progress compares model risk between comparable scans; it is not a laboratory lesion-area measurement.
- Research benchmark metrics bundled with the project are academic/synthetic benchmark results, not real-field deployment accuracy.
