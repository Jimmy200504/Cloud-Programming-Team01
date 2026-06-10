import { PackageOpen } from "lucide-react";
import { useState } from "react";
import { authenticateFace, retrieveFood, signalLock } from "../api/smartFridgeApi";
import { config } from "../config";
import { fileToBase64, imageContentType } from "../utils/fileToBase64";
import FilePreview from "./FilePreview";
import StatusBadge from "./StatusBadge";

export default function RetrieveFoodPanel({ session, onInventoryChanged, onResult }) {
  const [busy, setBusy] = useState(false);
  const [state, setState] = useState("Ready");
  const [faceFile, setFaceFile] = useState(null);
  const [foodFile, setFoodFile] = useState(null);
  const [form, setForm] = useState({ foodId: "", foodName: "" });

  async function handleSubmit(event) {
    event.preventDefault();
    setBusy(true);
    setState("Face auth");

    try {
      const faceAuth = await authenticateFace({
        action: "retrieve",
        imageContentType: imageContentType(faceFile),
        faceImageBase64: await fileToBase64(faceFile)
      });

      if (!faceAuth.authenticated) {
        setState("Denied");
        onResult({ workflow: "retrieve-food", faceAuth });
        return;
      }

      const recognizedUser = faceAuth.user || {};
      setState("Checking");
      const retrieveResult = await retrieveFood({
        foodId: form.foodId.trim(),
        foodName: form.foodName.trim(),
        actorUserId: recognizedUser.userId || session.user.userId,
        actorEmail: recognizedUser.email || session.user.email,
        userId: recognizedUser.userId || session.user.userId,
        actorDisplayName: recognizedUser.displayName || recognizedUser.email || "Recognized user",
        foodImageContentType: imageContentType(foodFile),
        foodImageBase64: await fileToBase64(foodFile)
      });

      const hardwareUnlock = retrieveResult.authorized
        ? await trySignalUnlock(session, "retrieve")
        : { requested: false, reason: "Ownership check denied" };

      setState(retrieveResult.authorized ? "Retrieved" : "Alert");
      onResult({
        workflow: "retrieve-food",
        faceAuth,
        hardwareUnlock,
        retrieveResult,
        hardwareAlert: retrieveResult.authorized
          ? { requested: false, reason: "Recognized user owns the food" }
          : { requested: true, actions: retrieveResult.hardwareActions || ["hardware-buzzer", "owner-email"] }
      });
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
          <p className="eyebrow">Egress</p>
          <h2>Retrieve Food Flow</h2>
        </div>
        <StatusBadge tone={busy ? "busy" : state === "Alert" ? "warning" : state === "Failed" || state === "Denied" ? "error" : "ready"}>
          {state}
        </StatusBadge>
      </div>

      <form className="flow-form" onSubmit={handleSubmit}>
        <FilePreview id="retrieve-face" label="Face image" accept="image/jpeg,image/jpg,image/png" file={faceFile} onChange={setFaceFile} required />
        <FilePreview id="retrieve-food" label="Food image" accept="image/jpeg,image/jpg,image/png" file={foodFile} onChange={setFoodFile} required />
        <label>
          Food id
          <input value={form.foodId} onChange={(event) => setForm({ ...form, foodId: event.target.value })} />
        </label>
        <label>
          Food name fallback
          <input value={form.foodName} onChange={(event) => setForm({ ...form, foodName: event.target.value })} />
        </label>
        <button type="submit" disabled={busy}>
          <PackageOpen size={18} />
          {busy ? "Running" : "Run retrieve flow"}
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
