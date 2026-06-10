import { UploadCloud } from "lucide-react";
import { useState } from "react";
import { uploadCurrentUserFace } from "../api/smartFridgeApi";
import { fileToBase64, imageContentType } from "../utils/fileToBase64";
import FilePreview from "./FilePreview";
import StatusBadge from "./StatusBadge";

export default function FaceRegistrationPanel({ session, onResult }) {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [state, setState] = useState("Ready");

  async function handleSubmit(event) {
    event.preventDefault();

    if (!session.idToken) {
      onResult({ success: false, errorCode: "NOT_SIGNED_IN", message: "Sign in before face registration" });
      return;
    }

    setBusy(true);
    setState("Uploading");
    try {
      const response = await uploadCurrentUserFace(session.idToken, {
        imageContentType: imageContentType(file),
        faceImageBase64: await fileToBase64(file)
      });
      setState("Stored");
      onResult(response);
    } catch (error) {
      setState("Failed");
      onResult(error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Biometrics</p>
          <h2>Face Registration</h2>
        </div>
        <StatusBadge tone={state === "Failed" ? "error" : busy ? "busy" : "ready"}>{state}</StatusBadge>
      </div>

      <form className="form-stack" onSubmit={handleSubmit}>
        <FilePreview
          id="face-register-image"
          label="Face image"
          accept="image/jpeg,image/jpg,image/png"
          file={file}
          onChange={setFile}
          required
        />
        <button type="submit" disabled={busy}>
          <UploadCloud size={18} />
          {busy ? "Uploading" : "Register face"}
        </button>
      </form>
    </section>
  );
}
