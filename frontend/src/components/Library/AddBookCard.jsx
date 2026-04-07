import UploadButton from "./UploadButton";

export default function AddBookCard({ onUploadComplete }) {
  return (
    <article style={cardShellStyle}>
      <UploadButton
        onUploadComplete={onUploadComplete}
        containerStyle={uploadContainerStyle}
        errorStyle={errorStyle}
        renderTrigger={({ openFilePicker, isUploading }) => (
          <button
            type="button"
            aria-label="Upload a new book"
            onClick={openFilePicker}
            style={addCardStyle}
          >
            <span style={plusStyle}>{isUploading ? "..." : "+"}</span>
            <span style={labelStyle}>{isUploading ? "Uploading book" : "Add book"}</span>
          </button>
        )}
      />
    </article>
  );
}

const cardShellStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.5rem",
};

const uploadContainerStyle = {
  width: "100%",
};

const addCardStyle = {
  width: "100%",
  minHeight: 320,
  aspectRatio: "0.76",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  gap: "0.85rem",
  border: "2px dashed rgba(23, 49, 62, 0.32)",
  borderRadius: 26,
  background: "rgba(255, 248, 239, 0.62)",
  color: "#17313e",
  cursor: "pointer",
  boxShadow: "0 22px 50px rgba(44, 33, 20, 0.08)",
};

const plusStyle = {
  display: "grid",
  placeItems: "center",
  width: 96,
  height: 96,
  borderRadius: 999,
  background: "#17313e",
  color: "#fff8ef",
  fontSize: "4.75rem",
  fontWeight: 300,
  lineHeight: 1,
};

const labelStyle = {
  fontSize: "1rem",
  fontWeight: 700,
};

const errorStyle = {
  margin: "0.5rem 0 0",
  color: "#a11d1d",
  fontSize: "0.84rem",
};
