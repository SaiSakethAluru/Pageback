export default function RecapLevelIndicator({ level }) {
  return (
    <div style={{ display: "flex", gap: 4 }}>
      {Array.from({ length: 5 }).map((_, index) => (
        <span
          key={index}
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            border: "1px solid rgba(67, 53, 39, 0.35)",
            background: index < level ? "#c89a4d" : "transparent",
            display: "inline-block",
          }}
        />
      ))}
    </div>
  );
}
