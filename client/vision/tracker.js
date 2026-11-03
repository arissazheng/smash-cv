// Camera + MediaPipe (web) -> LandmarkFrame. Owner: Person 1.
// LandmarkFrame JSON matches shared/landmarks.py LandmarkFrame.to_json: {t, pose, hands:[{side, lm, g, gs}]}.
import { FilesetResolver, PoseLandmarker, GestureRecognizer } from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";

const WASM = "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm";
const MODEL = "https://storage.googleapis.com/mediapipe-models";

export class Tracker {
  static async create(video, { width = 640, height = 480 } = {}) {
    const self = new Tracker();
    video.srcObject = await navigator.mediaDevices.getUserMedia({ video: { width, height } });
    await video.play();
    self.video = video;
    // Mirror into a canvas first (same as vision/camera.py), so handedness and x match the Python version.
    self.canvas = Object.assign(document.createElement("canvas"), { width: video.videoWidth, height: video.videoHeight });
    self.ctx = self.canvas.getContext("2d");
    const fileset = await FilesetResolver.forVisionTasks(WASM);
    self.pose = await PoseLandmarker.createFromOptions(fileset, {
      baseOptions: { modelAssetPath: `${MODEL}/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task`, delegate: "GPU" },
      runningMode: "VIDEO", numPoses: 1,
    });
    self.gestures = await GestureRecognizer.createFromOptions(fileset, {
      baseOptions: { modelAssetPath: `${MODEL}/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task`, delegate: "GPU" },
      runningMode: "VIDEO", numHands: 2,
    });
    return self;
  }

  /** Returns a LandmarkFrame, or null if no new camera frame yet. t is seconds. */
  process(nowMs = performance.now()) {
    const v = this.video;
    if (v.readyState < 2) return null;
    const { ctx, canvas } = this;
    ctx.save(); ctx.scale(-1, 1); ctx.drawImage(v, -canvas.width, 0); ctx.restore();
    const p = this.pose.detectForVideo(canvas, nowMs);
    const g = this.gestures.recognizeForVideo(canvas, nowMs);
    const pose = p.landmarks[0] ? p.landmarks[0].map((l) => [l.x, l.y, l.z, l.visibility ?? 0]) : null;
    const hands = g.landmarks.map((lm, i) => ({
      side: g.handedness[i]?.[0]?.categoryName ?? "Unknown",
      lm: lm.map((l) => [l.x, l.y, l.z]),
      g: g.gestures[i]?.[0]?.categoryName ?? "None",
      gs: g.gestures[i]?.[0]?.score ?? 0,
    }));
    return { t: nowMs / 1000, pose, hands };
  }
}
