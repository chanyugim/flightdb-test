import Typewriter from "./Typewriter";
import { chatSuggestions } from "../api/chatSuggestions";
import { chatDisplayMessage } from "../api/chatPresentation";
import { useCallback, useEffect, useRef, useState } from "react";
import { requestApi } from "../api/client";
import { useAuth } from "../context/AuthContext";
import ChatResults from "./ChatResults";
import ChatMessage from "./ChatMessage";
import "../chatbot.css";

export default function Chatbot() {
  const { token } = useAuth();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const context = useRef(null);
  const historyStart = useRef(0);
  const pending = useRef(null);
  const cooldown = useRef(0);
  const dialog = useRef(null);
  const scrollArea = useRef(null);
  const conversation = useRef(null);
  const followBottom = useRef(true);
  const onType = useCallback(() => {
    const area = scrollArea.current;
    if (followBottom.current && area) area.scrollTop = area.scrollHeight;
  }, []);

  const reset = () => {
    pending.current?.abort();
    pending.current = null;
    context.current = null;
    historyStart.current = 0;
    followBottom.current = true;
    setMessages([]);
    setInput("");
    setError("");
    setBusy(false);
  };

  useEffect(() => {
    reset();
    return () => pending.current?.abort();
  }, [token]);

  useEffect(() => {
    if (open) dialog.current?.showModal();
    else dialog.current?.close();
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    // 타이핑 완료 후 추가되는 결과 카드까지 따라가되, 이전 대화를 읽을 때는 이동하지 않음.
    const observer = new ResizeObserver(onType);
    observer.observe(conversation.current);
    onType();
    return () => observer.disconnect();
  }, [open, onType]);

  const send = async (question) => {
    question = question.trim();
    if (!question || pending.current) return;
    if (Date.now() < cooldown.current) {
      setError("요청이 많아요. 잠시 후 다시 보내 주세요.");
      return;
    }
    const controller = new AbortController();
    followBottom.current = true;
    pending.current = controller;
    setBusy(true);
    setError("");
    setInput("");
    const history = messages
      .slice(historyStart.current)
      .filter((m) => !m.failed)
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content.slice(0, 1000) }));
    const user = { role: "user", content: question };
    setMessages((prev) => [...prev, user]);
    try {
      const data = await requestApi("/chatbot/messages", {
        method: "POST",
        token,
        body: { question, limit: 5, history, context: context.current },
        signal: controller.signal,
      });
      if (pending.current !== controller) return;
      context.current = data.context;
      if (data.reset_search) historyStart.current = messages.length + 2;
      setMessages((prev) => [...prev, { role: "assistant", content: data.message, data }]);
    } catch (e) {
      if (pending.current !== controller || e.name === "AbortError") return;
      if (e.status === 429) cooldown.current = Date.now() + e.retryAfter * 1000;
      setMessages((prev) => prev.map((m) => (m === user ? { ...m, failed: true } : m)));
      setInput(question);
      setError(e.message);
    } finally {
      if (pending.current === controller) {
        pending.current = null;
        setBusy(false);
      }
    }
  };
  return (
    <>
      <button
        className="chat-launcher"
        aria-label="AI 챗봇 열기"
        aria-haspopup="dialog"
        onClick={() => setOpen(true)}
      >
        ✦<span>AI 챗봇</span>
      </button>
      <dialog
        ref={dialog}
        className="chat-dialog"
        aria-labelledby="chat-title"
        onCancel={() => setOpen(false)}
        onClose={() => setOpen(false)}
      >
        <div className="chat-header">
          <div>
            <strong id="chat-title">AI 여행 상담</strong>
            <small>항공편 일정은 한국 시간 기준으로 안내해요.</small>
          </div>
          <button autoFocus aria-label="챗봇 닫기" onClick={() => setOpen(false)}>
            ✕
          </button>
        </div>
        <div className="chat-tools">
          <button onClick={reset}>새 대화</button>
        </div>
        <div
          className="chat-messages"
          ref={scrollArea}
          onScroll={(e) => {
            const el = e.currentTarget;
            followBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
          }}
        >
          <div ref={conversation} className="chat-conversation">
            {!messages.length && (
              <ChatMessage>
                안녕하세요! 항공편, 왕복 일정, 프로모션을 함께 찾아드릴게요.
                <div className="chips">
                  {[
                    "다음 주 가장 저렴한 항공편을 보여줘",
                    "현재 프로모션을 알려줘",
                    "인기 노선을 알려줘",
                  ].map((q) => (
                    <button className="chat-suggestion" key={q} disabled={busy} onClick={() => send(q)}>
                      {q}
                    </button>
                  ))}
                </div>
              </ChatMessage>
            )}
            {messages.map((m, i) => (
              <ChatMessage role={m.role} key={i}>
                {m.role === "assistant" ? (
                  <Typewriter
                    text={m.data ? chatDisplayMessage(m.data) : m.content}
                    animate={i === messages.length - 1}
                  >
                    {m.data && (
                      <ChatResults data={m.data} close={() => setOpen(false)} send={send} busy={busy} />
                    )}
                    {m.data && i === messages.length - 1 && !busy && (
                      <div className="chat-suggestions" aria-label="추천 후속 질문">
                        {chatSuggestions(m.data).map((q) => (
                          <button className="chat-suggestion" key={q} onClick={() => send(q)}>
                            {q}
                          </button>
                        ))}
                      </div>
                    )}
                  </Typewriter>
                ) : (
                  <p>{m.content}</p>
                )}
                {m.failed && <small>전송 실패</small>}
              </ChatMessage>
            ))}
            {busy && (
              <ChatMessage thinking>
                <span>생각하는 중</span>
                <span className="thinking-dots" aria-hidden="true">
                  <i>.</i>
                  <i>.</i>
                  <i>.</i>
                </span>
                <span className="sr-only">답변을 준비하고 있어요.</span>
              </ChatMessage>
            )}
          </div>
        </div>
        {error && (
          <p className="error chat-error" role="alert">
            {error}
          </p>
        )}
        <form
          className="chat-input"
          onSubmit={(e) => {
            e.preventDefault();
            send(input);
          }}
        >
          <input
            aria-label="챗봇 질문"
            maxLength={1000}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="여행 조건을 자유롭게 말씀해 주세요"
          />
          <button className="btn-primary" disabled={busy || !input.trim()}>
            보내기
          </button>
        </form>
      </dialog>
    </>
  );
}
