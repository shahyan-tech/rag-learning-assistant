import { useEffect, useRef, useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

function App() {
  const [activeTab, setActiveTab] = useState("chat");

  const [question, setQuestion] = useState("");
  const [loadingChat, setLoadingChat] = useState(false);
  const [error, setError] = useState("");

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello. Ask me anything from your ML, DL, GenAI, or Agentic AI notes.",
      sources: [],
      answerType: "system",
      note: "",
    },
  ]);

  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);

  const chatEndRef = useRef(null);

  useEffect(() => {
    fetchChatSessions();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loadingChat]);

  async function fetchChatSessions() {
    setHistoryLoading(true);

    try {
      const response = await axios.get(`${API_BASE_URL}/chat/sessions`);
      setHistory(response.data || []);
    } catch (err) {
      console.error("Failed to fetch chat sessions:", err);
    } finally {
      setHistoryLoading(false);
    }
  }

  function startNewChat() {
    setCurrentSessionId(null);
    setQuestion("");
    setError("");

    setMessages([
      {
        role: "assistant",
        content:
          "Hello. Ask me anything from your ML, DL, GenAI, or Agentic AI notes.",
        sources: [],
        answerType: "system",
        note: "",
      },
    ]);
  }

  async function askQuestion() {
    const cleanQuestion = question.trim();

    if (!cleanQuestion) {
      setError("Please enter a question.");
      return;
    }

    setError("");
    setLoadingChat(true);
    setQuestion("");

    const userMessage = {
      role: "user",
      content: cleanQuestion,
      sources: [],
      answerType: "system",
      note: "",
    };

    setMessages((previous) => [...previous, userMessage]);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat/ask`, {
        question: cleanQuestion,
        n_results: 4,
        session_id: currentSessionId,
      });

      const assistantMessage = {
        role: "assistant",
        content: response.data.answer || "",
        sources: response.data.sources || [],
        answerType: response.data.answer_type || "system",
        note: response.data.note || "",
      };

      setCurrentSessionId(response.data.session_id);
      setMessages((previous) => [...previous, assistantMessage]);

      await fetchChatSessions();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        "Something went wrong while asking the chatbot.";

      setError(message);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: message,
          sources: [],
          answerType: "system",
          note: "",
        },
      ]);
    } finally {
      setLoadingChat(false);
    }
  }

  function handleEnterKey(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      askQuestion();
    }
  }

  async function openHistoryItem(item) {
    setActiveTab("chat");
    setError("");

    try {
      const response = await axios.get(
        `${API_BASE_URL}/chat/sessions/${item.id}`
      );

      setCurrentSessionId(response.data.id);

      const backendMessages = response.data.messages || [];

      const loadedMessages = backendMessages.map((message) => ({
        role: message.role || "assistant",
        content:
          message.content !== undefined && message.content !== null
            ? String(message.content)
            : "",
        sources: message.sources || [],
        answerType: message.answer_type || "system",
        note: message.note || "",
      }));

      if (loadedMessages.length === 0) {
        setMessages([
          {
            role: "assistant",
            content: "This chat session has no saved messages.",
            sources: [],
            answerType: "system",
            note: "",
          },
        ]);
      } else {
        setMessages(loadedMessages);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not load this chat session from the database."
      );
    }
  }

  async function deleteHistoryItem(sessionId) {
    try {
      await axios.delete(`${API_BASE_URL}/chat/sessions/${sessionId}`);

      if (currentSessionId === sessionId) {
        startNewChat();
      }

      await fetchChatSessions();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Could not delete this chat session."
      );
    }
  }

  async function clearHistory() {
    try {
      await Promise.all(
        history.map((item) =>
          axios.delete(`${API_BASE_URL}/chat/sessions/${item.id}`)
        )
      );

      startNewChat();
      await fetchChatSessions();
    } catch (err) {
      setError("Could not clear chat history.");
    }
  }

  return (
    <main className="app-shell">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <section className="main-area">
        {activeTab === "chat" && (
          <ChatScreen
            messages={messages}
            question={question}
            setQuestion={setQuestion}
            askQuestion={askQuestion}
            loadingChat={loadingChat}
            error={error}
            handleEnterKey={handleEnterKey}
            chatEndRef={chatEndRef}
            currentSessionId={currentSessionId}
            startNewChat={startNewChat}
          />
        )}

        {activeTab === "flashcards" && <FlashcardsScreen />}

        {activeTab === "mindmaps" && <MindMapsScreen />}

        {activeTab === "quizzes" && <QuizzesScreen />}

        {activeTab === "history" && (
          <HistoryScreen
            history={history}
            historyLoading={historyLoading}
            openHistoryItem={openHistoryItem}
            deleteHistoryItem={deleteHistoryItem}
            clearHistory={clearHistory}
          />
        )}

        {activeTab === "documents" && <DocumentsScreen />}

        {activeTab === "library" && <StudyLibraryScreen />}
      </section>
    </main>
  );
}

function Sidebar({ activeTab, setActiveTab }) {
  const items = [
    { id: "chat", label: "Chat", icon: "✦" },
    { id: "flashcards", label: "Flashcards", icon: "◇" },
    { id: "mindmaps", label: "Mind Maps", icon: "◎" },
    { id: "quizzes", label: "Quizzes", icon: "✓" },
    { id: "history", label: "History", icon: "↺" },
    { id: "documents", label: "Documents", icon: "▣" },
    { id: "library", label: "Study Library", icon: "◈" },
  ];

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">R</div>
        <div>
          <h1>RAG Tutor</h1>
          <p>Learn from your own notes</p>
        </div>
      </div>

      <nav className="nav-list">
        {items.map((item) => (
          <button
            key={item.id}
            className={activeTab === item.id ? "nav-item active" : "nav-item"}
            onClick={() => setActiveTab(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-card">
        <p className="mini-label">System</p>
        <strong>RAG enabled</strong>
        <span>FastAPI · Chroma · Groq · SQLite</span>
      </div>
    </aside>
  );
}

function ChatScreen({
  messages,
  question,
  setQuestion,
  askQuestion,
  loadingChat,
  error,
  handleEnterKey,
  chatEndRef,
  currentSessionId,
  startNewChat,
}) {
  return (
    <div className="workspace chat-workspace">
      <header className="topbar">
        <div>
          <p className="section-kicker">Chat</p>
          <h2>Ask your AI learning assistant</h2>
        </div>

        <div className="topbar-actions">
          <div className="status-pill">
            <span className="status-dot"></span>
            {currentSessionId ? `Session #${currentSessionId}` : "New chat"}
          </div>

          <button className="light-action compact-action" onClick={startNewChat}>
            New Chat
          </button>
        </div>
      </header>

      <section className="chat-window">
        {messages.map((message, index) => (
          <MessageBubble key={`${message.role}-${index}`} message={message} />
        ))}

        {loadingChat && (
          <div className="message-row assistant-row">
            <div className="avatar assistant-avatar">AI</div>
            <div className="message-bubble assistant-bubble">
              <p className="typing">
                Reading your notes and preparing an answer...
              </p>
            </div>
          </div>
        )}

        <div ref={chatEndRef}></div>
      </section>

      {error && <div className="error-box">{error}</div>}

      <section className="composer">
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={handleEnterKey}
          placeholder="Ask anything from your ML, DL, GenAI, or Agentic AI notes..."
          rows={2}
        />

        <button onClick={askQuestion} disabled={loadingChat}>
          {loadingChat ? "Thinking" : "Send"}
        </button>
      </section>
    </div>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === "user";

  const safeContent =
    message.content !== undefined && message.content !== null
      ? String(message.content)
      : "No message content found.";

  return (
    <div
      className={isUser ? "message-row user-row" : "message-row assistant-row"}
    >
      <div
        className={isUser ? "avatar user-avatar" : "avatar assistant-avatar"}
      >
        {isUser ? "You" : "AI"}
      </div>

      <div
        className={
          isUser
            ? "message-bubble user-bubble"
            : "message-bubble assistant-bubble"
        }
      >
        {!isUser && message.answerType && message.answerType !== "system" && (
          <div
            className={
              message.answerType === "notes"
                ? "answer-type-badge notes-badge"
                : "answer-type-badge general-badge"
            }
          >
            {message.answerType === "notes"
              ? "Answered from uploaded notes"
              : "General AI answer"}
          </div>
        )}

        {!isUser && message.note && (
          <div className="answer-note">{message.note}</div>
        )}

        <p>{safeContent}</p>

        <SourcesPanel sources={message.sources} />
      </div>
    </div>
  );
}

function SourcesPanel({ sources }) {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="sources-panel">
      <p className="source-title">Sources</p>

      <div className="source-list">
        {sources.map((source, index) => (
          <div
            className="source-chip"
            key={`${source.source}-${source.location}-${index}`}
          >
            <strong>{source.source}</strong>
            <span>
              part {source.location}
              {typeof source.distance === "number"
                ? ` · ${source.distance.toFixed(3)}`
                : ""}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function FlashcardsScreen() {
  const [topic, setTopic] = useState("normal equation");
  const [count, setCount] = useState(5);
  const [flashcards, setFlashcards] = useState([]);
  const [sources, setSources] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showBack, setShowBack] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [artifactId, setArtifactId] = useState(null);



  async function generateFlashcards() {
    if (!topic.trim()) {
      setError("Please enter a topic.");
      return;
    }

    setLoading(true);
    setError("");
    setFlashcards([]);
    setSources([]);
    setCurrentIndex(0);
    setShowBack(false);

    try {
      const response = await axios.post(`${API_BASE_URL}/study/flashcards`, {
        topic,
        count: Number(count),
        n_results: 4,
      });

      setFlashcards(response.data.flashcards || []);
      setSources(response.data.sources || []);
      setArtifactId(response.data.artifact_id);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Something went wrong while generating flashcards."
      );
    } finally {
      setLoading(false);
    }
  }

  const currentCard = flashcards[currentIndex];

  function nextCard() {
    setShowBack(false);
    setCurrentIndex((previous) =>
      previous === flashcards.length - 1 ? 0 : previous + 1
    );
  }

  function previousCard() {
    setShowBack(false);
    setCurrentIndex((previous) =>
      previous === 0 ? flashcards.length - 1 : previous - 1
    );
  }

  return (
    <div className="workspace">
      <ToolHeader
        kicker="Flashcards"
        title="Generate active-recall cards"
        subtitle="Create clean question-answer cards from your uploaded learning notes."
      />

      <section className="tool-grid">
        <div className="control-card">
          <label>Topic</label>
          <input
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Example: gradient descent"
          />

          <label>Number of cards</label>
          <select
            value={count}
            onChange={(event) => setCount(event.target.value)}
          >
            <option value={3}>3 cards</option>
            <option value={5}>5 cards</option>
            <option value={10}>10 cards</option>
          </select>

          <button
            className="primary-action"
            onClick={generateFlashcards}
            disabled={loading}
          >
            {loading ? "Generating..." : "Generate Flashcards"}
          </button>

          {artifactId && (
  <div className="success-box">
    Saved to Study Library as item #{artifactId}
  </div>
)}

          {error && <div className="error-box">{error}</div>}
          <SourcesPanel sources={sources} />
        </div>

        <div className="result-card">
          {flashcards.length === 0 ? (
            <EmptyState
              title="No flashcards yet"
              text="Enter a topic and generate cards from your notes."
            />
          ) : (
            <>
              <div className="card-counter">
                Card {currentIndex + 1} of {flashcards.length}
              </div>

              <button
                className="flashcard"
                onClick={() => setShowBack(!showBack)}
              >
                <span>{showBack ? "Answer" : "Question"}</span>
                <h3>{showBack ? currentCard.back : currentCard.front}</h3>
                <p>Click to flip</p>
              </button>

              <div className="card-controls">
                <button onClick={previousCard}>Previous</button>
                <button onClick={nextCard}>Next</button>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
}

function MindMapsScreen() {
  const [topic, setTopic] = useState("linear regression");
  const [mindMap, setMindMap] = useState(null);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [artifactId, setArtifactId] = useState(null);

  async function generateMindMap() {
    if (!topic.trim()) {
      setError("Please enter a topic.");
      return;
    }

    setLoading(true);
    setError("");
    setMindMap(null);
    setSources([]);

    try {
      const response = await axios.post(`${API_BASE_URL}/study/mindmap`, {
        topic,
        n_results: 5,
      });

      setMindMap(response.data.mind_map);
      setSources(response.data.sources || []);
      setArtifactId(response.data.artifact_id);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Something went wrong while generating the mind map."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="workspace">
      <ToolHeader
        kicker="Mind Maps"
        title="Turn notes into a topic map"
        subtitle="Generate a structured view of concepts, subtopics, and relationships."
      />

      <section className="tool-grid">
        <div className="control-card">
          <label>Topic</label>
          <input
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Example: transformers"
          />

          <button
            className="primary-action"
            onClick={generateMindMap}
            disabled={loading}
          >
            {loading ? "Generating..." : "Generate Mind Map"}
          </button>

          {artifactId && (
  <div className="success-box">
    Saved to Study Library as item #{artifactId}
  </div>
)}

          {error && <div className="error-box">{error}</div>}
          <SourcesPanel sources={sources} />
        </div>

        <div className="result-card">
          {!mindMap ? (
            <EmptyState
              title="No mind map yet"
              text="Enter a topic and generate a structured concept map."
            />
          ) : (
            <div className="mindmap-canvas">
              <MindMapNode node={mindMap} level={0} />
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function MindMapNode({ node, level }) {
  return (
    <div className={`mind-node level-${level}`}>
      <div className="mind-node-title">{node.title}</div>

      {node.children && node.children.length > 0 && (
        <div className="mind-node-children">
          {node.children.map((child, index) => (
            <MindMapNode
              key={`${child.title}-${index}`}
              node={child}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function QuizzesScreen() {
  const [topic, setTopic] = useState("normal equation");
  const [count, setCount] = useState(5);
  const [difficulty, setDifficulty] = useState("beginner");
  const [questions, setQuestions] = useState([]);
  const [sources, setSources] = useState([]);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [artifactId, setArtifactId] = useState(null);

  async function generateQuiz() {
    if (!topic.trim()) {
      setError("Please enter a topic.");
      return;
    }

    setLoading(true);
    setError("");
    setQuestions([]);
    setSources([]);
    setSelectedAnswers({});
    setSubmitted(false);

    try {
      const response = await axios.post(`${API_BASE_URL}/study/quiz`, {
        topic,
        count: Number(count),
        difficulty,
        n_results: 4,
      });

      setQuestions(response.data.questions || []);
      setSources(response.data.sources || []);
      setArtifactId(response.data.artifact_id);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Something went wrong while generating the quiz."
      );
    } finally {
      setLoading(false);
    }
  }

  function chooseAnswer(questionIndex, option) {
    if (submitted) return;

    setSelectedAnswers((previous) => ({
      ...previous,
      [questionIndex]: option,
    }));
  }

  const score = questions.reduce((total, question, index) => {
    return selectedAnswers[index] === question.correct_answer ? total + 1 : total;
  }, 0);

  return (
    <div className="workspace">
      <ToolHeader
        kicker="Quizzes"
        title="Practice with AI-generated MCQs"
        subtitle="Generate quizzes from your notes and check your understanding."
      />

      <section className="tool-grid">
        <div className="control-card">
          <label>Topic</label>
          <input
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Example: CNN basics"
          />

          <label>Questions</label>
          <select
            value={count}
            onChange={(event) => setCount(event.target.value)}
          >
            <option value={3}>3 questions</option>
            <option value={5}>5 questions</option>
            <option value={10}>10 questions</option>
          </select>

          <label>Difficulty</label>
          <select
            value={difficulty}
            onChange={(event) => setDifficulty(event.target.value)}
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>

          <button
            className="primary-action"
            onClick={generateQuiz}
            disabled={loading}
          >
            {loading ? "Generating..." : "Generate Quiz"}
          </button>

          {artifactId && (
  <div className="success-box">
    Saved to Study Library as item #{artifactId}
  </div>
)}

          {questions.length > 0 && (
            <button
              className="secondary-action"
              onClick={() => setSubmitted(true)}
              disabled={submitted}
            >
              Submit Quiz
            </button>
          )}

          {submitted && (
            <div className="score-box">
              Score: {score} / {questions.length}
            </div>
          )}

          {error && <div className="error-box">{error}</div>}
          <SourcesPanel sources={sources} />
        </div>

        <div className="result-card quiz-result-card">
          {questions.length === 0 ? (
            <EmptyState
              title="No quiz yet"
              text="Enter a topic and generate questions from your notes."
            />
          ) : (
            <div className="quiz-list">
              {questions.map((quizQuestion, questionIndex) => (
                <div
                  className="quiz-question"
                  key={`${quizQuestion.question}-${questionIndex}`}
                >
                  <h3>
                    {questionIndex + 1}. {quizQuestion.question}
                  </h3>

                  <div className="options-list">
                    {quizQuestion.options.map((option) => {
                      const selected = selectedAnswers[questionIndex] === option;
                      const isCorrect =
                        submitted && option === quizQuestion.correct_answer;
                      const isWrong =
                        submitted &&
                        selected &&
                        option !== quizQuestion.correct_answer;

                      let className = "option-button";

                      if (selected) className += " selected";
                      if (isCorrect) className += " correct";
                      if (isWrong) className += " wrong";

                      return (
                        <button
                          key={option}
                          className={className}
                          onClick={() => chooseAnswer(questionIndex, option)}
                        >
                          {option}
                        </button>
                      );
                    })}
                  </div>

                  {submitted && (
                    <p className="explanation">
                      <strong>Explanation:</strong> {quizQuestion.explanation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function DocumentsScreen() {
  const [documents, setDocuments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);

  const [loadingDocs, setLoadingDocs] = useState(false);
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [loadingIndex, setLoadingIndex] = useState(false);

  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  async function fetchDocuments() {
    setLoadingDocs(true);
    setError("");

    try {
      const response = await axios.get(`${API_BASE_URL}/documents/raw`);
      setDocuments(response.data.documents || []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not load documents from the backend."
      );
    } finally {
      setLoadingDocs(false);
    }
  }

  async function uploadDocument() {
    if (!selectedFile) {
      setError("Please select a file first.");
      return;
    }

    setLoadingUpload(true);
    setError("");
    setSuccessMessage("");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/documents/upload`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setSuccessMessage(response.data.message);
      setSelectedFile(null);
      await fetchDocuments();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Something went wrong while uploading the document."
      );
    } finally {
      setLoadingUpload(false);
    }
  }

  async function indexDocuments() {
    setLoadingIndex(true);
    setError("");
    setSuccessMessage("");

    try {
      const response = await axios.post(`${API_BASE_URL}/documents/index`);

      setSuccessMessage(
        `Indexed ${response.data.indexed_chunks} chunks. Total vectors: ${response.data.total_vectors}`
      );

      await fetchDocuments();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Something went wrong while indexing documents."
      );
    } finally {
      setLoadingIndex(false);
    }
  }

  useEffect(() => {
    fetchDocuments();
  }, []);

  return (
    <div className="workspace">
      <ToolHeader
        kicker="Documents"
        title="Manage your knowledge base"
        subtitle="Upload your PDFs, PowerPoint slides, notebooks, markdown files, and text notes. Then index them so the assistant can use them."
      />

      <section className="tool-grid">
        <div className="control-card">
          <label>Upload learning material</label>

          <input
            type="file"
            accept=".pdf,.pptx,.ipynb,.txt,.md"
            onChange={(event) => setSelectedFile(event.target.files[0])}
          />

          {selectedFile && (
            <div className="selected-file">
              Selected: <strong>{selectedFile.name}</strong>
            </div>
          )}

          <button
            className="primary-action"
            onClick={uploadDocument}
            disabled={loadingUpload}
          >
            {loadingUpload ? "Uploading..." : "Upload Document"}
          </button>

          <button
            className="secondary-action"
            onClick={indexDocuments}
            disabled={loadingIndex}
          >
            {loadingIndex ? "Indexing..." : "Index Documents"}
          </button>

          <button
            className="light-action"
            onClick={fetchDocuments}
            disabled={loadingDocs}
          >
            {loadingDocs ? "Refreshing..." : "Refresh List"}
          </button>

          {error && <div className="error-box">{error}</div>}

          {successMessage && (
            <div className="success-box">{successMessage}</div>
          )}
        </div>

        <div className="result-card">
          <div className="documents-header">
            <div>
              <p className="section-kicker">Uploaded Files</p>
              <h3>{documents.length} document(s)</h3>
            </div>
          </div>

          {documents.length === 0 ? (
            <EmptyState
              title="No documents uploaded"
              text="Upload a small PDF, PPTX, notebook, markdown, or text file to begin."
            />
          ) : (
            <div className="documents-list">
              {documents.map((document) => (
                <div className="document-item" key={document.file_name}>
                  <div className="document-icon">
                    {document.file_type.toUpperCase()}
                  </div>

                  <div>
                    <strong>{document.file_name}</strong>
                    <span>
                      {document.file_type.toUpperCase()} · {document.size_kb} KB
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}


function StudyLibraryScreen() {
  const [artifacts, setArtifacts] = useState([]);
  const [selectedArtifact, setSelectedArtifact] = useState(null);

  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");

  async function fetchArtifacts() {
    setLoadingList(true);
    setError("");

    try {
      const response = await axios.get(`${API_BASE_URL}/study/artifacts`);
      setArtifacts(response.data || []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not load saved study artifacts."
      );
    } finally {
      setLoadingList(false);
    }
  }

  async function openArtifact(artifactId) {
    setLoadingDetail(true);
    setError("");

    try {
      const response = await axios.get(
        `${API_BASE_URL}/study/artifacts/${artifactId}`
      );

      setSelectedArtifact(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not open this study artifact."
      );
    } finally {
      setLoadingDetail(false);
    }
  }

  async function deleteArtifact(artifactId) {
    setError("");

    try {
      await axios.delete(`${API_BASE_URL}/study/artifacts/${artifactId}`);

      if (selectedArtifact?.id === artifactId) {
        setSelectedArtifact(null);
      }

      await fetchArtifacts();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Could not delete this study artifact."
      );
    }
  }

  useEffect(() => {
    fetchArtifacts();
  }, []);

  return (
    <div className="workspace">
      <ToolHeader
        kicker="Study Library"
        title="Saved flashcards, quizzes, and mind maps"
        subtitle="Reopen study material that was generated earlier and saved in the database."
      />

      <section className="tool-grid">
        <div className="control-card">
          <button
            className="light-action"
            onClick={fetchArtifacts}
            disabled={loadingList}
          >
            {loadingList ? "Refreshing..." : "Refresh Library"}
          </button>

          {error && <div className="error-box">{error}</div>}

          <div className="artifact-list">
            {artifacts.length === 0 ? (
              <EmptyState
                title="No saved study material"
                text="Generate flashcards, quizzes, or mind maps first. They will appear here."
              />
            ) : (
              artifacts.map((artifact) => (
                <div className="artifact-item" key={artifact.id}>
                  <button onClick={() => openArtifact(artifact.id)}>
                    <span>{artifact.artifact_type}</span>
                    <strong>{artifact.topic}</strong>
                    <p>{new Date(artifact.created_at).toLocaleString()}</p>
                  </button>

                  <button
                    className="delete-artifact-button"
                    onClick={() => deleteArtifact(artifact.id)}
                  >
                    Delete
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="result-card">
          {loadingDetail ? (
            <EmptyState
              title="Opening saved item"
              text="Loading study material from the database..."
            />
          ) : !selectedArtifact ? (
            <EmptyState
              title="Select a saved item"
              text="Choose flashcards, a quiz, or a mind map from the left."
            />
          ) : (
            <SavedArtifactViewer artifact={selectedArtifact} />
          )}
        </div>
      </section>
    </div>
  );
}


function SavedArtifactViewer({ artifact }) {
  if (artifact.artifact_type === "flashcards") {
    return <SavedFlashcards artifact={artifact} />;
  }

  if (artifact.artifact_type === "quiz") {
    return <SavedQuiz artifact={artifact} />;
  }

  if (artifact.artifact_type === "mindmap") {
    return <SavedMindMap artifact={artifact} />;
  }

  return (
    <EmptyState
      title="Unknown study item"
      text="This saved artifact type is not supported yet."
    />
  );
}

function SavedFlashcards({ artifact }) {
  const flashcards = artifact.payload?.flashcards || [];
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showBack, setShowBack] = useState(false);

  const currentCard = flashcards[currentIndex];

  function nextCard() {
    setShowBack(false);
    setCurrentIndex((previous) =>
      previous === flashcards.length - 1 ? 0 : previous + 1
    );
  }

  function previousCard() {
    setShowBack(false);
    setCurrentIndex((previous) =>
      previous === 0 ? flashcards.length - 1 : previous - 1
    );
  }

  if (flashcards.length === 0) {
    return (
      <EmptyState
        title="No flashcards found"
        text="This saved flashcard artifact has no cards."
      />
    );
  }

  return (
    <div>
      <div className="saved-artifact-header">
        <span>Flashcards</span>
        <h3>{artifact.topic}</h3>
      </div>

      <div className="card-counter">
        Card {currentIndex + 1} of {flashcards.length}
      </div>

      <button className="flashcard" onClick={() => setShowBack(!showBack)}>
        <span>{showBack ? "Answer" : "Question"}</span>
        <h3>{showBack ? currentCard.back : currentCard.front}</h3>
        <p>Click to flip</p>
      </button>

      <div className="card-controls">
        <button onClick={previousCard}>Previous</button>
        <button onClick={nextCard}>Next</button>
      </div>

      <SourcesPanel sources={artifact.sources} />
    </div>
  );
}

function SavedQuiz({ artifact }) {
  const questions = artifact.payload?.questions || [];

  if (questions.length === 0) {
    return (
      <EmptyState
        title="No quiz questions found"
        text="This saved quiz artifact has no questions."
      />
    );
  }

  return (
    <div>
      <div className="saved-artifact-header">
        <span>Quiz</span>
        <h3>{artifact.topic}</h3>
      </div>

      <div className="quiz-list">
        {questions.map((question, index) => (
          <div className="quiz-question" key={`${question.question}-${index}`}>
            <h3>
              {index + 1}. {question.question}
            </h3>

            <div className="options-list">
              {question.options.map((option) => {
                const isCorrect = option === question.correct_answer;

                return (
                  <button
                    key={option}
                    className={
                      isCorrect
                        ? "option-button correct"
                        : "option-button"
                    }
                  >
                    {option}
                  </button>
                );
              })}
            </div>

            <p className="explanation">
              <strong>Explanation:</strong> {question.explanation}
            </p>
          </div>
        ))}
      </div>

      <SourcesPanel sources={artifact.sources} />
    </div>
  );
}

function SavedMindMap({ artifact }) {
  const mindMap = artifact.payload?.mind_map;

  if (!mindMap) {
    return (
      <EmptyState
        title="No mind map found"
        text="This saved mind map artifact has no map data."
      />
    );
  }

  return (
    <div>
      <div className="saved-artifact-header">
        <span>Mind Map</span>
        <h3>{artifact.topic}</h3>
      </div>

      <div className="mindmap-canvas">
        <MindMapNode node={mindMap} level={0} />
      </div>

      <SourcesPanel sources={artifact.sources} />
    </div>
  );
}


function HistoryScreen({
  history,
  historyLoading,
  openHistoryItem,
  deleteHistoryItem,
  clearHistory,
}) {
  return (
    <div className="workspace">
      <header className="topbar">
        <div>
          <p className="section-kicker">History</p>
          <h2>Saved chat sessions</h2>
          <p className="section-subtitle">
            These chats are loaded from your backend SQLite database.
          </p>
        </div>

        {history.length > 0 && (
          <button className="danger-button" onClick={clearHistory}>
            Clear All
          </button>
        )}
      </header>

      <section className="history-panel">
        {historyLoading ? (
          <EmptyState
            title="Loading history"
            text="Fetching saved chat sessions from the database..."
          />
        ) : history.length === 0 ? (
          <EmptyState
            title="No saved chats yet"
            text="Ask a question in Chat. It will be saved here automatically."
          />
        ) : (
          history.map((item) => (
            <div className="history-card" key={item.id}>
              <button
                className="history-item"
                onClick={() => openHistoryItem(item)}
              >
                <span>Session #{item.id}</span>
                <strong>{item.title}</strong>
                <p>
                  {item.message_count} message(s) · Updated{" "}
                  {new Date(item.updated_at).toLocaleString()}
                </p>
              </button>

              <button
                className="delete-session-button"
                onClick={() => deleteHistoryItem(item.id)}
              >
                Delete
              </button>
            </div>
          ))
        )}
      </section>
    </div>
  );
}

function ToolHeader({ kicker, title, subtitle }) {
  return (
    <header className="topbar">
      <div>
        <p className="section-kicker">{kicker}</p>
        <h2>{title}</h2>
        <p className="section-subtitle">{subtitle}</p>
      </div>
    </header>
  );
}

function EmptyState({ title, text }) {
  return (
    <div className="empty-state">
      <div>
        <div className="empty-icon">✦</div>
        <h3>{title}</h3>
        <p>{text}</p>
      </div>
    </div>
  );
}

export default App;