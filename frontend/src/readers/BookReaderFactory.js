export function getReaderType(filename) {
  const lowered = filename.toLowerCase();
  if (lowered.endsWith(".epub")) {
    return "epub";
  }
  if (lowered.endsWith(".pdf")) {
    return "pdf";
  }
  return null;
}
