export function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.addEventListener("load", () => {
      const value = String(reader.result || "");
      resolve(value.includes(",") ? value.split(",")[1] : value);
    });

    reader.addEventListener("error", () => reject(reader.error));
    reader.readAsDataURL(file);
  });
}

export function audioContentType(file) {
  if (file?.type) return file.type;

  const extension = file?.name?.split(".").pop()?.toLowerCase();
  return (
    {
      wav: "audio/wav",
      mp3: "audio/mpeg",
      mp4: "audio/mp4",
      m4a: "audio/x-m4a",
      flac: "audio/flac",
      ogg: "audio/ogg",
      amr: "audio/amr",
      webm: "audio/webm"
    }[extension] || "audio/mpeg"
  );
}

export function imageContentType(file) {
  return file?.type || "image/jpeg";
}
