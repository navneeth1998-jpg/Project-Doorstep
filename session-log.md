# Session Log — Doormat Package Detector

Short, bullet-based entries per session. Timestamped. Skimmable, not essay-style.

---

## 2026-07-03
- Set up project folder: `doormat-detector`
- Created `CLAUDE.md` with project rules (secrets, git behavior, code quality, comms style)
- Added auto-update policy + build status checklist + Update Log to `CLAUDE.md`
- Created this `session-log.md` for ongoing session notes
- Status: no code written yet — next step is environment setup (Python, dependencies, `.env`)

## 2026-07-06
- Installed Python 3.12.10 alongside pre-existing 3.14 (3.14 too new for ML packages)
- Created `venv` virtual environment using Python 3.12, fixed PowerShell execution policy blocking activation
- Installed `ultralytics` 8.4.89 and `opencv-python` 5.0.0.93 in venv
- Wrote `detect_photo.py`: captures one webcam photo, runs YOLOv8 nano, saves annotated image + logs test results to session-log.md
- Ran first two test detections: backpack held up → detected "person" (0.85); phone on carpet → detected "mouse" (0.31, wrong)
- Added `test_images/` subfolder, script now saves timestamped output files there instead of overwriting one file
- Created `linkedin-moments.md` for tracking shareable project moments (loose/plain-English trigger, documented in CLAUDE.md)
- Raspberry Pi setup: recovered a stuck microSD card during flashing, confirmed first successful ping + SSH login over home WiFi
- Set up SSH key-based login (ed25519) from laptop to Pi (`nava-pi.local`) — no more password needed
- Confirmed this session can run remote commands on the Pi over SSH (verified Pi's Python version: 3.13.5)
- Status: local dev environment + YOLOv8 detection working on laptop; Pi is reachable and remotely controllable via SSH key auth. Next: get camera hardware working on the Pi itself.

## 2026-07-06 (cont.) — Camera Module 3 bring-up
- Camera Module 3 initially not detected (`rpicam-hello --list-cameras` → "No cameras available")
- Diagnosed via dmesg (no sensor logged) and I2C bus scan (bus 13/14 showed a floating-bus pattern, not a real device)
- Root cause: ribbon cable orientation wrong on both ends — Pi 5 CAM0 requires metal contacts facing the Ethernet port (opposite of older Pi models), and the camera-module end requires contacts facing the camera's own PCB (opposite of the Pi end)
- Fixed both ends after confirming correct orientation against official Raspberry Pi documentation
- `rpicam-hello --list-cameras` now detects sensor: `imx708`, 4608x2592, at I2C address 0x1a
- Took first test photo directly on the Pi (`rpicam-still`), copied to laptop as `test_images/pi_camera_first_test.jpg`
- Status: Pi camera hardware confirmed fully working end-to-end (detect + capture). Next: get YOLOv8 detection running on Pi-captured images.

## 2026-07-06 (cont.) — Python environment on the Pi
- Created `~/doormat-venv` virtual environment on the Pi (Python 3.13.5, aarch64, Debian 13 trixie)
- First install attempt (`pip install ultralytics opencv-python`) failed with "No space left on device" — root cause: default `torch` pulled in a full NVIDIA CUDA/GPU toolkit (~1.5GB+ of unnecessary packages for a Pi with no NVIDIA GPU), which filled the Pi's small 2GB RAM-backed `/tmp` partition mid-download
- Fixed by installing the CPU-only `torch`/`torchvision` build explicitly from PyTorch's CPU package index first (150MB, vs 1.5GB+), then installing `ultralytics`/`opencv-python` on top — reused the CPU torch with no further issues
- Final versions: `ultralytics` 8.4.90, `opencv-python` 5.0.0.93, `torch` 2.12.1+cpu, `torchvision` 0.27.1+cpu
- Noted: Pi installs used piwheels.org (Raspberry Pi-specific pre-built ARM packages), so most installs were fast pre-built downloads rather than slow from-source compiles
- Status: Pi now has a working Python environment with YOLOv8 + OpenCV installed. Next: run detection on a Pi-captured photo.

## 2026-07-09 — First YOLOv8 detection using the Pi camera
- Adapted `detect_photo.py` into `detect_photo_pi.py`: replaces `cv2.VideoCapture` (laptop webcam) with `picamera2` (Pi CSI camera) for capture; detection/logging logic unchanged
- Had to enable `include-system-site-packages = true` in the Pi's venv config so it could see the system-installed `picamera2`/`libcamera` bindings (apt package, not pip-installable)
- Ran over SSH: captured a soccer ball on a cream carpet against a white door
- Result: no objects detected at all (YOLOv8 nano's COCO training set doesn't cover "soccer ball" well, and low-contrast round object may not have registered)
- Inference time: 2.63s wall-clock (includes ~2.2s one-time model load/warm-up overhead); core detection math itself was 427.8ms per Ultralytics' internal log
- Pi camera captured at full 4608x2592 (12MP), much higher than typical laptop webcam resolution
- File: `test_images/detection_pi_2026-07-09_170653.jpg`
- Status: Pi camera + YOLOv8 pipeline confirmed working end-to-end on-device. Next: test with more doormat-realistic objects (actual delivery box) and decide on a confidence threshold before designing notification logic.

## 2026-07-09 (cont.) — Cardboard box test on Pi camera
- Scene: white cuboidal cardboard box against a blue background with a red base for contrast
- Result: 3 objects detected, all misclassified — "book" (0.82), "bed" (0.37), "couch" (0.34); no "box"/"package" label since YOLOv8 nano's COCO training set has no such category
- Inference time: 1.43s wall-clock; core detection math 271.0ms (comparable to soccer ball test's 427.8ms — normal run-to-run variance)
- File: `test_images/detection_pi_2026-07-09_171506.jpg`
- Key takeaway: YOLOv8 nano out-of-the-box has no "package" concept — flat/rectangular objects get misread as book/bed/couch depending on angle. Confirms the project will need either custom fine-tuning on package images, or simpler "any new/unexpected object appeared" logic instead of relying on a specific label match.
- Status: two real-object baseline tests done (soccer ball: nothing detected; box: wrong labels but non-trivial confidence). Next: decide detection strategy (custom-trained class vs. generic object-appeared logic) before building notification pipeline.

## 2026-07-09 (cont.) — Object-count comparison logic + sequence test
- Goal: since YOLO can't reliably *name* a package, tested whether it could still be useful by just counting "some confident object present" and comparing photo-to-photo, instead of relying on the label
- Took 3 manual phone photos (not Pi camera) of the same doorstep spot: zero items, one item, two items — saved to `test_images/` (`doorstep_zero items.jpeg`, `doorstep_one item.jpeg`, `doorstep_two items.jpeg`)
- Wrote `compare_sequence.py`: runs YOLOv8 nano on all 3, counts detections above a 0.4 confidence threshold per photo, compares consecutive photos to report "arrived" / "arrived again" / "no change"
- Raw results (no threshold applied): zero-item photo → nothing detected at all; one-item photo → nothing detected at all; two-item photo → 1 "book" at 0.303 confidence (below our 0.4 cutoff, and only 1 detection despite 2 physical objects)
- Key finding: this is worse than a naming problem — YOLO isn't just mislabeling the objects, it's frequently failing to notice them at all, and confidence doesn't scale with object count
- Caught a bug in `compare_sequence.py`'s comparison logic: a count *decrease* (package picked up) was being silently lumped into "no change" instead of its own event — needs fixing to a proper 3-way (or 4-way) outcome: arrived / arrived again / picked up / no change
- Also clarified a misstatement from earlier discussion: the "don't rely on YOLO naming the object" approach is already what `compare_sequence.py` does (counts by confidence, ignores label) — the real unresolved problem is detection *sensitivity*, not naming
- Status: confirmed YOLOv8 nano out-of-the-box is not reliable enough for this project's core use case (low detection rate, low confidence, no count scaling). Next session should start here: (1) fix the count-decrease bug in `compare_sequence.py`, (2) decide between lowering the confidence threshold vs. fine-tuning YOLO on real package/doorstep photos — fine-tuning is looking increasingly necessary given how often the model misses the object entirely.

## 2026-07-11 — First YOLOv8 fine-tuning attempt (Roboflow dataset v1)
- Unzipped Roboflow export `Doormat Detector.v1i.yolov8.zip` — 1 class ("package"), 110 train images, 28 valid images, 0 test images
- Wrote `train_package_detector.py`: fine-tunes YOLOv8 nano, up to 100 epochs, early stopping patience=20, imgsz=640
- Training stopped early at epoch 24 (best checkpoint was epoch 4); took ~18 minutes on laptop CPU
- Final validation metrics (best.pt): precision 0.521, recall 0.697, mAP50 0.696, mAP50-95 0.485 — real improvement over stock YOLOv8n (which detected packages almost never)
- Wrote `validate_package_detector.py`: runs best.pt against all 28 valid images, saves annotated output to `training images/validation_results/`
- Result at default confidence settings: 0 detections on all 28 validation images
- Investigated why, given the decent mAP score: raw confidence check (threshold disabled) showed every image produces 300 candidate boxes, but every single one under 5.5% confidence — the model learned a faint *ranking* signal (correct location scores marginally higher than background, enough to earn mAP credit) but did not learn to be genuinely confident. This is a realistic outcome for fine-tuning on only 110 images, not a broken run.
- Model weights saved at `runs/detect/training images/runs/package_detector/weights/best.pt`
- Status: v1 fine-tune technically "learned something" (real ranking signal) but is not usable for real detection — confidence outputs too weak to threshold against. Conclusion: need meaningfully more training data. Next: user is preparing a much larger (9,555 image) merged dataset from Roboflow Universe sources for a v2 fine-tune.

## 2026-07-11 (cont.) — Dataset v2: class consolidation (9,555 images)
- Unzipped merged Roboflow Universe dataset (9,555 images, 27 raw class names — different sources used different labels for the same real-world object)
- Reviewed instance counts per class; user confirmed intent to merge all 27 into one class, no exclusions (including edge-case classes like `backpack`, `suitcase`, `label`, `flyer` — accepted as-is per user's explicit instruction, despite earlier flags that these could be noisy)
- Wrote `remap_classes_to_package.py`: rewrote class ID to `0` across all 9,555 label files (7,644 train + 1,911 valid), left box coordinates untouched
- Updated `data.yaml`: `nc: 1`, `names: ['package']`
- Verified: only class ID 0 exists across every label file; spot-checked 3 sample images with drawn boxes to visually confirm remap correctness
- Dataset ready at `training images/Combined package images.v1/`

## 2026-07-18 — Attempted v2 local training, found CPU too slow, moved to Colab
- Confirmed no usable local GPU (AMD integrated graphics only, no CUDA support) — training would run on CPU
- Ran a 1-epoch timing test with optimized settings (imgsz=512, batch=32) on the full 9,555-image dataset: 42.3 minutes for just 1 epoch. Note: explicitly setting `workers=8` had no effect — Ultralytics silently falls back to 0 dataloader workers on Windows, a platform limitation, not fixable via config.
- Realistic local estimate: 14-70+ hours for a full run. Decided to move training to Google Colab (free GPU) instead of running locally overnight.
- Prepared full Colab walkthrough for user: Drive upload, notebook cells (mount Drive, unzip, install ultralytics, confirm GPU, train with matching settings, copy results back to Drive)
- Re-zipped the class-consolidated dataset (`Combined_package_images_v1_consolidated.zip`, ~1.18GB) for upload to Drive

## 2026-07-22 — v2 fine-tune results (trained via Colab GPU by roommate) — SUCCESS
- Roommate ran the training in Colab using the prepared dataset/settings; sent back `package_detector_v2-20260722T234659Z-1-001.zip` containing full training results
- Unzipped into `training images/package_detector_v2_results/`; copied weights to permanent location `training images/models/package_v2_best.pt`
- Verified `args.yaml`: config matches exactly as planned (epochs=100, patience=20, batch=32, imgsz=512, device='0' GPU, correct dataset path) — confirms this is a legitimate, correctly-configured run, not a mismatched/altered one
- All 100 epochs completed (no early stopping triggered), took ~4.5 hours total on Colab's GPU (vs. 14-70+ hour local CPU estimate)
- Verified best epoch (85) metrics directly from `results.csv`: precision 0.873, recall 0.785, mAP50 0.875, mAP50-95 0.725 — closely matches what user was told, confirms legitimate results
- Wrote `validate_package_detector_v2.py`: ran the model against all 1,911 validation images
- **Critical result — real confidence scores, unlike v1**: at the standard 0.25 confidence threshold, 96.2% of validation images produced at least one detection (only 3.8% zero-detection, vs. 100% zero-detection in v1's default-threshold run). Median best-detection confidence per image: 0.933. 94.5% of images had a best detection >= 0.50 confidence; 72.2% had a best detection >= 0.90 confidence.
- This is a categorical improvement over v1 (which topped out around 5.5% confidence on any detection, anywhere) — the model has moved from "faint ranking signal only" to "genuinely confident, usable detections"
- Saved annotated validation outputs to `training images/validation_results_v2/`
- Status: v2 model is a real, usable package detector for the first time in this project. Next: deploy to the Pi (copy weights over, update the Pi detection script to load this fine-tuned model instead of stock yolov8n.pt, re-test with the live Pi camera).

## 2026-07-22 (cont.) — Zero-detection spot-check + real doorstep test + Pi script prep
- Identified and renamed the 73 validation images (out of 1,911) where the v2 model produced zero detections at the 0.25 threshold, to `no_result_1.jpg` ... `no_result_73.jpg` in `validation_results_v2/` for easy manual review — noted these files still show faint sub-threshold boxes since they were originally rendered at a near-zero confidence threshold
- Ran the v2 model against the 3 real doorstep photos (`test_images/doorstep_zero items.jpeg`, `doorstep_one item.jpeg`, `doorstep_two items.jpeg`) — the closest thing to a true real-world test so far (actual doorstep background, not dataset images): zero-item photo correctly detected nothing; one-item photo detected 1 package at 88.1% confidence; two-item photo detected 2 separate packages at 92.7% and 91.6% confidence. Correct count and high confidence on all 3, no false positives. Saved as `test_images/v2_detection_doorstep_*.jpg`
- Updated `detect_photo_pi.py` to use the fine-tuned model (`training images/models/package_v2_best.pt`) instead of stock `yolov8n.pt`, with confidence threshold set to 0.5
- **0.5 threshold reasoning**: based on validation confidence distribution (94.5% of images had a best detection above 0.5), and leaning loose deliberately — a false alarm (unnecessary notification) is low-cost and easily ignored, while a missed real package defeats the entire point of the project. Documented in-code as a starting hypothesis, not yet confirmed against real Pi camera photos; flagged as likely needing adjustment once tested live.
- Not yet transferred to the Pi — script is ready locally, deployment (copying model + script over SSH) is pending until user is physically home and connected to the Pi
- Status: local prep complete for Pi deployment. Next: once home, transfer `package_v2_best.pt` and updated `detect_photo_pi.py` to the Pi, re-test with the live Pi camera, and revisit the 0.5 threshold based on real results.

## 2026-07-24 — First live end-to-end success at the actual doorstep
- Moved the Pi to the doorstep (new power socket); safely shut down and relocated, reconnected to WiFi with zero issues
- Transferred `package_v2_best.pt` and updated `detect_photo_pi.py` to the Pi (matching relative folder structure so the script's model path resolves correctly); verified file size matched exactly post-transfer, no corruption
- Ran the fine-tuned model live on the Pi camera at the real doorstep, with a real orange package present: **detected "package" at 87% confidence** — correct, and comfortably above the 0.5 threshold
- This is the first fully live, end-to-end success: Pi camera → fine-tuned model → correct, confident detection, at the actual deployment location, no laptop involved
- Inference time: 2.30s (consistent with prior Pi timing measurements)
- File: `test_images/detection_pi_2026-07-24_202343.jpg`
- Status: core detection pipeline is proven working end-to-end at the real doorstep. Next: test more real scenarios (multiple packages, different lighting/times of day, empty doormat) to build confidence before moving to notification logic (Telegram/Pushover).

## 2026-07-24 (cont.) — 6 new real doorstep photos: weaker confidence, flagged for later
- Ran `package_v2_best.pt` on 6 new real doorstep photos (IMG_5500-5506, varied package counts/positions and real sunlight/shadow conditions), saved to `test_images/real_doorstep_test/`
- Result: 0 detections on all 6 at the 0.5 threshold — but raw (unfiltered) top confidence per photo ranged 0.082-0.496, meaning the model saw *something* in the right ballpark but not confidently enough to clear the bar
- One clear outlier: IMG_5505 at only 0.082 raw confidence, notably weaker than the other 5 (0.28-0.50) — flagged for the user to cross-check against that photo's specific lighting condition
- Confirmed EXIF orientation normal on all 6 (ruled out a sideways-image bug); real cause likely lighting/shadow and/or phone camera angle differing from the Pi's fixed top-down mount, not yet root-caused
- Explicitly deferred: this investigation is a separate track from the comparison-logic work below, not blocking it

## 2026-07-24 (cont.) — Comparison logic (arrived/picked up/no change) verified end-to-end
- Fixed two carried-over issues in `compare_sequence.py`: (1) was still using stock `yolov8n.pt` instead of the fine-tuned `package_v2_best.pt`; (2) the count-decrease bug flagged back on 2026-07-09 (a picked-up package silently reported as "no change") was never actually fixed, only flagged — fixed now with a proper "picked up" branch. Threshold aligned to our established 0.5.
- Test 1 (forward order: zero → one → two, the original confirmed-working sequence): detected 0 → 1 → 2 packages correctly at each step. Comparison output: zero→one = "arrived", one→two = "arrived again" — correctly handled the second-package-while-first-still-present case this logic was originally designed for.
- Test 2 (reverse order: two → one → zero, to specifically exercise the decrease path): detected 2 → 1 → 0 correctly. Comparison output: two→one = "picked up", one→zero = "picked up" — confirms the fix works correctly in both directions, not just in code review.
- Status: comparison logic (arrived / arrived again / picked up / no change) is now verified working end-to-end in both directions on real, trustworthy detections. Next: decide how this logic will run continuously on the Pi (polling interval, how "previous count" gets persisted between runs) before building notification logic on top.

## 2026-07-24 (cont.) — Continuous monitoring core logic (check/remember/compare) built and stress-tested
- Built `monitor_check.py`: reusable check-once function (photo -> detect -> load last count from `package_state.json` -> compare -> save new count). No notification logic yet — detection/comparison only.
- Test A (logic correctness): re-ran the zero/one/two real sequence through the new persistent-state version — correctly produced baseline "no change" -> "arrived" -> "arrived again", matching prior verified behavior.
- Test B (stamina test): ran the same check logic across 100 validation images (selected via sorted filenames + `random.seed(42)` + `random.sample`, chosen over alphabetical-first-100 to avoid clustering bias from same-source image batches), with a temporary 1.5s interval instead of the real 30s, to test code robustness rather than meaningful event detection. Result: 100/100 cycles completed, 0 errors, 69 change events detected, 69 images saved to `test_images/stamina_test_output/` — all numbers internally consistent, verified saved file count on disk matches reported count. Check interval reset to 30s afterward, confirmed.
- Status: check/remember/compare logic is proven reliable under repeated use. Next: wire this into an actual continuous loop on the Pi (camera capture + this logic, running every 30s) before adding notifications.

## 2026-07-27 — Telegram notifications: connection confirmed working
- Set up `.env` (with `.gitignore` protecting it) for `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`, per project secrets convention — installed `python-dotenv` and `requests`
- Bot created via BotFather: "Package Detector" (`@Package_Detector_bot`)
- Chat ID discovery required some troubleshooting: first two attempts to fetch it via `getUpdates` came back empty despite user confirming messages were sent to the correct bot directly (not a group, no webhook interfering per `getWebhookInfo`) — resolved on a third attempt after user fully opened the chat and re-sent; root cause not conclusively identified, but bot identity (`getMe`) and webhook status were verified clean throughout, ruling out a token/config issue
- Wrote `get_telegram_chat_id.py` (one-time chat ID discovery helper) and `test_telegram_message.py` (sends one confirmation message)
- Sent test message, user confirmed receipt on their phone — Telegram messaging is fully working end-to-end
- Status: Telegram notification channel is ready to wire into the detection/monitoring logic. Not yet connected to `monitor_check.py` — that integration is the next step, along with deciding what message text/content to send on each event type (arrived/arrived again/picked up).

## 2026-07-27 (cont.) — Detection + Telegram wired together, confirmed live
- Extracted `send_message` into a shared `telegram_notify.py` module (avoids duplicating the Telegram-sending code between the original test script and the monitoring logic)
- Updated `monitor_check.py`: `check_once` now sends a Telegram notification automatically whenever a real event occurs (arrived / arrived again / picked up), with event-specific message text including current package count where relevant. "No change" events send nothing, by design.
- Re-ran the zero/one/two real photo sequence through this updated logic — user confirmed on their phone: exactly 2 messages received, in order ("A package has arrived..." then "Another package has arrived — there are now 2 packages..."), and correctly zero messages for the baseline "no change" step
- Status: first fully working slice of the real system — detect, compare, and notify are now connected end-to-end (tested with real detections, not live camera yet). Not yet tested: "picked up" notification wording (logic verified earlier, but not through the live Telegram-connected path), and the "attach the actual photo" enhancement is intentionally deferred. Next: wire this into a real continuous loop on the Pi camera.

## 2026-07-27 (cont.) — "Picked up" notification verified live, gap closed
- Ran the same 3 real photos in reverse order (two → one → zero items) through the live Telegram-connected `check_once` path
- Result: baseline "no change" on first step (no message, correct), then two consecutive "picked up" events — user confirmed 2 messages received on Telegram, correct text and remaining-count each time ("...1 package(s) remaining", then "...0 package(s) remaining")
- Status: all four event types (arrived, arrived again, picked up, no change) are now verified through the real, live, connected detect->compare->notify path, not just underlying logic. Text-notification piece of the system is complete. Next: wire into a real continuous loop on the Pi camera (photo capture -> check_once -> repeat every 30s).

## 2026-07-28 — Live continuous Pi camera loop: first fully unattended end-to-end success
- Built `pi_continuous_monitor.py`: captures from the Pi camera (not static files), runs `check_once` from `monitor_check.py` each cycle, saves each frame to `test_images/`, sleeps 30s (production interval), repeats for a bounded number of cycles (test-only cap, not an infinite loop yet)
- Transferred `monitor_check.py`, `telegram_notify.py`, and `.env` to the Pi (installed `python-dotenv` there too); set `.env` permissions to `600` (owner-only read/write) on the Pi for security
- First attempt (10 cycles, ~5 min): interrupted partway through at user's request — process had to be force-killed via PID after `pkill` pattern-match failed to catch it; confirmed cleanly stopped afterward
- Second attempt (shortened to 5 cycles, ~2 min): completed cleanly, but count stayed at 0 across all 5 cycles — investigated by pulling back all 5 saved frames and re-running detection at a low (0.05) threshold: every frame showed a weak "package" detection in the 5.6%-38.1% range, never crossing the 0.5 threshold. This connects directly to the previously-flagged real-doorstep confidence problem (IMG_5500-5506 test) rather than being a new issue — same root cause showing up again.
- Third attempt (same 5-cycle, ~2 min test, rerun): **succeeded** — cycle 5 correctly detected the package arriving (count 0->1), fired an "arrived" event, and sent a real Telegram notification with zero manual triggering. User confirmed receipt on their phone.
- Status: **first fully live, unattended, end-to-end success** — real Pi camera, real detection, real comparison logic, real Telegram notification, no human in the loop except placing the package. Confirms the core system works. Still open: the real-world confidence problem (weak detections in actual doorstep lighting/positioning, sometimes below threshold) is a recurring, not one-off, issue — worth prioritizing next now that it's shown up 3 times (6-photo test, first 2-min attempt, and implicitly here too). Also still needed: converting the bounded-cycle test script into a true always-on infinite loop for real deployment.
- User context on the confidence issue: this test was done handheld (camera not yet physically mounted with the planned fixture/duct-tape setup), single-person operation juggling laptop commands + holding the Pi/camera + throwing the package into frame — real camera shake, shifting angle, and inconsistent framing likely explain much of the weak/inconsistent confidence, separate from any model quality issue. Deprioritized further confidence investigation until after physical mounting gives a stable, consistent camera position to test against.

## 2026-07-28 (cont.) — Telegram notifications now include the photo, not just text
- Added `send_photo()` to `telegram_notify.py` (Telegram's `sendPhoto` API, image + caption in one message, rather than two separate messages)
- Updated `monitor_check.py`: `notify_if_real_event` now sends the actual captured photo with the event text as its caption, replacing the text-only message
- Tested locally with the zero/one/two sequence — user confirmed both notifications arrived as photo+caption, not separate text
- Transferred updated `monitor_check.py` and `telegram_notify.py` to the Pi
- Status: notifications now include visual proof of the event, not just text. Not yet re-tested live on the Pi camera loop specifically (only tested via the static local sequence) — worth a quick live confirmation next time the Pi loop runs. Next: convert `pi_continuous_monitor.py` into a true always-on infinite loop, and revisit confidence tuning once the camera is physically mounted.

## 2026-07-28 (cont.) — Pre-release cleanup: audit, consolidation, repo organization
- Full audit of all 16 Python files: 3 form the live system (`pi_continuous_monitor.py`, `monitor_check.py`, `telegram_notify.py`), 3 are evidence/regression tests worth keeping (`test_a_logic_correctness.py`, `test_b_stamina.py`, `validate_package_detector_v2.py`), 10 are historical/superseded (early detection scripts, v1 training/validation, dataset prep one-offs, Telegram onboarding helpers)
- Confirmed the live system already had a single clear entry point (`pi_continuous_monitor.py`) — no logic changes needed, just organization
- Moved historical scripts to `archive/`, evidence/test scripts to `tests/`; fixed cross-module imports broken by the move (`sys.path` insertion so `monitor_check.py`/`telegram_notify.py` remain importable from their new relative location) rather than leaving them silently broken
- Decision: kept `pi_continuous_monitor.py` bounded (test-cap, not a true infinite loop) as a deliberate scope choice for this stage of the project — to be documented explicitly in the README as a known boundary, not an oversight
- Surveyed full project size (~4.6GB) and updated `.gitignore` to exclude large datasets/zips/bulk test images/results while keeping the final model (`package_v2_best.pt`, 6.2MB), training metrics (`results.csv`, `args.yaml`), and a few small illustrative folders
- Created `docs/demo_images/` with 5 curated images spanning the project's arc: the original backpack-as-person failure, the fine-tuned model correctly counting 2 packages, the real live Pi doorstep detection, a dataset class-consolidation spot-check, and the final training curves
- Considered renaming `training images/` (space in folder name) for cleanliness — decided against it: the path is baked into the *deployed* Pi script (`monitor_check.py`), so renaming would require also renaming the folder on the Pi and re-validating the live path right before filming a demo, for a purely cosmetic gain (the space has never actually caused a bug, since all references go through `Path()`/proper quoting). Documented as a known, intentional quirk instead.
- Ran secrets check: exhaustive search across the entire project (including the dataset) confirmed the Telegram bot token and chat ID exist only in `.env`, which is correctly gitignored
- Ran `git init` + dry-run staging preview (no actual commit) to validate repo size before pushing: caught and fixed two real issues in the process — a `.gitignore` pattern that wasn't matching a nested subfolder (would have staged several MB of redundant training plots) and Claude Code's own local settings file (`.claude/settings.local.json`) being swept in unintentionally. Final result: 32 files, ~7MB total would be staged — a fast, clean, appropriately-sized repo.
- Re-ran the zero/one/two sequence test from its new `tests/` location to validate the reorganization didn't break anything — identical correct results to every prior run, real Telegram photo notification confirmed received by user
- Status: pre-release cleanup complete and validated. Next: write the README, then git commit and push to GitHub.

## 2026-07-28 (cont.) — README written, pushed to GitHub — project reaches technical completion
- Wrote a comprehensive README covering: motivation (tied to the theft frustration + Walmart PII background), architecture, technical decisions with real reasoning (top-down camera, fine-tuning rationale, 0.5 threshold, WhatsApp data-sourcing decision), real v1-vs-v2 results table, real challenges (SD card, camera cable orientation, 27-class fragmentation, GPU quota), deliberate scope decisions (bounded loop, `training images/` naming), skills demonstrated, and run-it-yourself instructions
- Revised after user feedback: added an early "Status" line clarifying this is a completed learning project, not a live deployment; tightened the skills list and challenges section (~20%); removed unnecessary detail from the Colab GPU section; removed one embedded image from Real Results per user preference; verified the 85% backpack-misclassification figure against session-log.md directly rather than trusting memory
- Considered and explicitly declined renaming `training images/` (space in folder name) before push — the path is baked into the deployed Pi script, so renaming would require re-validating the live system for a purely cosmetic gain; documented as an intentional, known quirk in the README instead
- `git init`, staged and committed 33 files (32 from the earlier dry-run + README.md itself)
- Created GitHub repo (`navneeth1998-jpg/Project-Doorstep`, public, no auto-generated README/.gitignore/license to avoid conflicts), connected as `origin`, pushed `main` successfully
- Status: **project reaches a genuine, clean state of technical completion.** Live system, tests, full history, and documentation are all on GitHub. Known, explicitly-scoped next steps for anyone continuing this: convert the monitoring loop to a true always-on service, and revisit detection confidence tuning once the camera has a stable physical mount.

## 2026-07-28 (cont.) — Demo video recordings + picked-up notification changed to text-only
- Removed `linkedin-moments.md` from the GitHub repo (kept locally, added to `.gitignore`) — internal content notes, not project documentation. Confirmed via `git ls-tree` against the actual pushed GitHub state (not just local) that it's gone, and separately re-confirmed `.env` has never been tracked anywhere, on GitHub or locally.
- Recorded demo footage: ran the real zero→one sequence (laptop-only, Pi safely shut down first) twice via screen recording, both times correctly triggering a live "arrived" Telegram notification with photo — second take succeeded after the user's first recording attempt failed
- User flagged that "picked up" should be text-only (no photo) — this was a genuine design correction, not a misunderstanding of existing behavior: all three event types were currently sending a photo. Updated `monitor_check.py`: `arrived`/`arrived again` keep the photo, `picked up` now sends text-only via `send_message` instead of `send_photo`
- Verified live: one→zero sequence correctly triggered "picked up" as a text-only Telegram message, no photo attached, recorded successfully
- Not yet synced to the Pi (currently powered off/unplugged) — `monitor_check.py` needs to be re-copied over next time the Pi is back online so the deployed system matches this change. Not yet committed/pushed to GitHub either.
- Status: notification behavior now intentionally differentiated by event type (photo for arrivals, text-only for pickups). Remaining before this change is fully "live everywhere": sync to Pi, commit and push to GitHub.
