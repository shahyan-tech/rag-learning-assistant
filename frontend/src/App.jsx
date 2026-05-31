import { useState } from "react";
import axios from "axios";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [question, setQuestion] = useState(
    "What is the normal equation in linear regression?"
  );
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function askQuestion() {
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }

    setLoading(true);
    setError("");
    setAnswer("");
    setSources([]);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat/ask`, {
        question: question,
        n_results: 4,
      });

      setAnswer(response.data.answer);
      setSources(response.data.sources || []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Something went wrong while asking the chatbot."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">RAG Learning Assistant</p>
        <h1>Learn ML, DL, GenAI, and Agentic AI from your own notes.</h1>
        <p className="subtitle">
          Ask questions from your uploaded PDFs, PPTX files, and notebooks.
          The assistant answers with source references.
        </p>
      </section>

      <section className="chat-card">
        <label htmlFor="question">Ask a question</label>

        <textarea
          id="question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Example: Explain gradient descent in simple words."
          rows={4}
        />

        <button onClick={askQuestion} disabled={loading}>
          {loading ? "Thinking..." : "Ask Assistant"}
        </button>

        {error && <div className="error">{error}</div>}

        {answer && (
          <section className="answer-box">
            <h2>Answer</h2>
            <p>{answer}</p>
          </section>
        )}

        {sources.length > 0 && (
          <section className="sources-box">
            <h2>Sources</h2>

            <ul>
              {sources.map((source, index) => (
                <li key={`${source.source}-${source.location}-${index}`}>
                  <strong>{source.source}</strong> — part {source.location}
                  <span>distance: {source.distance.toFixed(4)}</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </section>
    </main>
  );
}

export default App;