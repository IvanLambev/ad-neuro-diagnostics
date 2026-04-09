const MAX_DURATION_SECONDS = 60;

export const ACCEPTED_VIDEO_EXTENSIONS = [".mp4", ".mov", ".mkv", ".avi", ".webm"];

export async function inspectVideoFile(file: File) {
  const extension = `.${file.name.split(".").pop()?.toLowerCase() ?? ""}`;
  if (!ACCEPTED_VIDEO_EXTENSIONS.includes(extension)) {
    throw new Error(`Use one of these formats: ${ACCEPTED_VIDEO_EXTENSIONS.join(", ")}.`);
  }

  const durationSeconds = await readDuration(file);
  if (durationSeconds > MAX_DURATION_SECONDS) {
    throw new Error("Ads longer than 60 seconds are not supported yet.");
  }

  return {
    durationSeconds,
    extension,
  };
}

function readDuration(file: File) {
  return new Promise<number>((resolve, reject) => {
    const video = document.createElement("video");
    const objectUrl = URL.createObjectURL(file);

    video.preload = "metadata";
    video.onloadedmetadata = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(video.duration);
    };
    video.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("We could not read the video duration. Try another file."));
    };
    video.src = objectUrl;
  });
}
