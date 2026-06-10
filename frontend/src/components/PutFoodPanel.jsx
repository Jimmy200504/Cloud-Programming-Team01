import { PackagePlus, Wand2 } from "lucide-react";
import { useState } from "react";
import { authenticateFace, parseExpiration, putFood, signalLock } from "../api/smartFridgeApi";
import { config } from "../config";
import { defaultExpirationDate } from "../utils/format";
import { audioContentType, fileToBase64, imageContentType } from "../utils/fileToBase64";
import FilePreview from "./FilePreview";
import StatusBadge from "./StatusBadge";

export default function PutFoodPanel({ session, onInventoryChanged, onResult }) {
  const [busy, setBusy] = useState(false);
  const [state, setState] = useState("Ready");
  const [faceFile, setFaceFile] = useState(null);
  const [foodFile, setFoodFile] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [form, setForm] = useState({
    foodName: "milk",
    expirationDate: defaultExpirationDate(7),
    expirationTranscript: "兩週後"
  });

  async function handleParseExpiration() {
    setBusy(true);
    setState("Parsing");
    try {
      const body = form.expirationTranscript.trim()
        ? { expirationTranscript: form.expirationTranscript.trim() }
        : {
            audioContentType: audioContentType(audioFile),
            expirationAudioBase64: await fileToBase64(audioFile)
          };
      const response = await parseExpiration(body);
      setForm((current) => ({
        ...current,
        expirationDate: response.expiration?.expirationDate || current.expirationDate
      }));
      onResult(response);
      setState("Ready");
    } catch (error) {
      setState("Failed");
      onResult(error);
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setState("Face auth");

    try {
      const faceAuth = await authenticateFace({
        action: "put",
        imageContentType: imageContentType(faceFile),
        faceImageBase64: await fileToBase64(faceFile)
      });

      if (!faceAuth.authenticated) {
        setState("Denied");
        onResult({ workflow: "put-food", faceAuth });
        return;
      }

      setState("Unlocking");
      const unlock = await trySignalUnlock(session, "put");
      const recognizedUser = faceAuth.user || {};
      const now = new Date().toISOString();
      const body = {
        foodName: form.foodName.trim(),
        ownerEmail: recognizedUser.email || session.user.email,
        userId: recognizedUser.userId || session.user.userId,
        ownerUserId: recognizedUser.userId || session.user.userId,
        expirationDate: form.expirationDate,
        capturedAt: now,
        putAt: now,
        timezone: config.timezone,
        recordType: "react-dashboard-put-flow"
      };

      if (foodFile) {
        body.foodImageContentType = imageContentType(foodFile);
        body.foodImageBase64 = await fileToBase64(foodFile);
      }

      if (form.expirationTranscript.trim()) {
        body.expirationTranscript = form.expirationTranscript.trim();
      } else if (audioFile) {
        body.audioContentType = audioContentType(audioFile);
        body.expirationAudioBase64 = await fileToBase64(audioFile);
      }

      setState("Storing");
      const createdFood = await putFood(body);
      setState("Stored");
      onResult({ workflow: "put-food", faceAuth, hardwareUnlock: unlock, storedFood: createdFood.food });
      await onInventoryChanged();
    } catch (error) {
      setState("Failed");
      onResult(error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel flow-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Ingress</p>
          <h2>Put Food Flow</h2>
        </div>
        <StatusBadge tone={busy ? "busy" : state === "Failed" || state === "Denied" ? "error" : "ready"}>{state}</StatusBadge>
      </div>

      <form className="flow-form" onSubmit={handleSubmit}>
        <FilePreview id="put-face" label="Face image" accept="image/jpeg,image/jpg,image/png" file={faceFile} onChange={setFaceFile} required />
        <FilePreview id="put-food" label="Food image" accept="image/jpeg,image/jpg,image/png" file={foodFile} onChange={setFoodFile} />
        <label>
          Food name
          <input value={form.foodName} onChange={(event) => setForm({ ...form, foodName: event.target.value })} />
        </label>
        <label>
          Expiration date
          <input
            type="date"
            required
            value={form.expirationDate}
            onChange={(event) => setForm({ ...form, expirationDate: event.target.value })}
          />
        </label>
        <label className="wide-field">
          Expiration transcript
          <input
            value={form.expirationTranscript}
            onChange={(event) => setForm({ ...form, expirationTranscript: event.target.value })}
          />
        </label>
        <FilePreview
          id="put-audio"
          label="Expiration audio"
          accept="audio/*,.wav,.mp3,.m4a,.mp4,.flac,.ogg,.amr,.webm"
          file={audioFile}
          onChange={setAudioFile}
          audio
        />
        <button className="ghost-button" type="button" disabled={busy || (!form.expirationTranscript.trim() && !audioFile)} onClick={handleParseExpiration}>
          <Wand2 size={18} />
          Parse date
        </button>
        <button type="submit" disabled={busy}>
          <PackagePlus size={18} />
          {busy ? "Running" : "Run put flow"}
        </button>
      </form>
    </section>
  );
}

async function trySignalUnlock(session, reason) {
  const signal = {
    requested: true,
    type: "unlock-fridge-lock",
    reason,
    deviceId: config.defaultDeviceId
  };

  if (!session.idToken) {
    return {
      ...signal,
      sent: false,
      message: "No signed-in session token"
    };
  }

  try {
    return {
      ...signal,
      sent: true,
      response: await signalLock(session.idToken, "unlocked")
    };
  } catch (error) {
    return {
      ...signal,
      sent: false,
      error: {
        message: error.message,
        ...(error.payload || {})
      }
    };
  }
}
