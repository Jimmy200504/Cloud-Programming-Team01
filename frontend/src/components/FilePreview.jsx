import { Camera, FileAudio, ImagePlus } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

export default function FilePreview({ id, label, accept, file, onChange, required, audio = false }) {
  const [previewUrl, setPreviewUrl] = useState("");

  useEffect(() => {
    if (!file || audio) {
      setPreviewUrl("");
      return undefined;
    }

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [audio, file]);

  const meta = useMemo(() => {
    if (!file) return audio ? "Audio input" : "Image input";
    const size = file.size > 1024 * 1024 ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(file.size / 1024)} KB`;
    return `${file.name} / ${size}`;
  }, [audio, file]);

  return (
    <label className="file-control" htmlFor={id}>
      <span>{label}</span>
      <input
        id={id}
        type="file"
        accept={accept}
        required={required}
        onChange={(event) => onChange(event.target.files?.[0] || null)}
      />
      <span className={`file-preview ${previewUrl ? "has-image" : ""}`}>
        {previewUrl ? (
          <img src={previewUrl} alt="" />
        ) : audio ? (
          <FileAudio size={22} />
        ) : file ? (
          <Camera size={22} />
        ) : (
          <ImagePlus size={22} />
        )}
        <small>{meta}</small>
      </span>
    </label>
  );
}
