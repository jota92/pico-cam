import express from "express";
import fs from "fs";
import path from "path";
import crypto from "crypto";

const app = express();
const PORT = process.env.PORT || 3000;
const DEVICE_TOKEN = process.env.DEVICE_TOKEN || "replace-with-device-token";
const UPLOAD_DIR = process.env.UPLOAD_DIR || "./uploads";
fs.mkdirSync(UPLOAD_DIR, { recursive: true });

app.use(express.raw({ type: ["image/jpeg", "application/octet-stream"], limit: "4mb" }));

app.post("/upload", async (req, res) => {
  const token = req.header("x-device-token") || "";
  if (token !== DEVICE_TOKEN) return res.status(401).json({ ok: false, error: "bad token" });
  if (!req.body || req.body.length < 100) return res.status(400).json({ ok: false, error: "empty image" });

  const id = new Date().toISOString().replace(/[:.]/g, "-") + "-" + crypto.randomBytes(4).toString("hex");
  const filename = path.join(UPLOAD_DIR, `${id}.jpg`);
  fs.writeFileSync(filename, req.body);

  // OpenAI API call should be done here on the server, never from the device.
  // Keep the API key only in server environment variables.
  res.json({ ok: true, id, bytes: req.body.length });
});

app.get("/health", (_, res) => res.json({ ok: true }));
app.listen(PORT, () => console.log(`CameraIoT server listening on ${PORT}`));
