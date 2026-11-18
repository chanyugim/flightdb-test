export default function ChatMessage({ role = "assistant", thinking = false, children }) {
  return (
    <div className={`chat-message ${role}`}>
      <div className="chat-author">
        {role === "assistant" && (
          <span className="chat-avatar" aria-hidden="true">
            ✦
          </span>
        )}
        <span>{role === "assistant" ? "AI 여행 상담" : "나"}</span>
      </div>
      <div
        className={`chat-bubble ${role}${thinking ? " thinking" : ""}`}
        role={thinking ? "status" : undefined}
      >
        {children}
      </div>
    </div>
  );
}
