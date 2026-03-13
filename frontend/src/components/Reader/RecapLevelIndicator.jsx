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
            border: "1px solid rgba(255,255,255,0.9)",
            background: index < level ? "#f2d18f" : "transparent",
            display: "inline-block",
          }}
        />
      ))}
    </div>
  );
}
