import { useState } from 'react'
import './App.css'

const QUESTIONS = [
  "What’s your primary investment goal (growth, income, or preservation)?",
  "What’s your target time horizon (e.g. 3, 5, or 10+ years)?",
  "On a scale of 1–5, how would you rate your risk tolerance?",
  "What is the approximate size of your current portfolio (in USD)?",
  "Which major asset classes do you hold today (e.g. US Equity, Bonds, Crypto)?",
  "Do you have any sector or geographic constraints/preferences?",
  "How much cash or liquidity buffer do you want to keep available?",
  "Do you have any ethical or sustainable investing preferences?",
  "How sensitive are you to fees (low, medium, high)?",
  "How often would you like to rebalance (monthly, quarterly, annually)?"
];

function App() {
  const [answers, setAnswers] = useState(
    QUESTIONS.reduce((acc, q) => ({ ...acc, [q]: '' }), {})
  );
  const [step, setStep] = useState('survey'); // 'survey' | 'done' | 'recommend'
  const [recommendation, setRecommendation] = useState('');

  const sessionId =
    localStorage.getItem('sessionId') ||
    crypto.randomUUID().replace(/-/g, '');

  localStorage.setItem('sessionId', sessionId);

  const handleChange = (q, value) => {
    setAnswers(a => ({ ...a, [q]: value }));
  }

  const handleSubmit = async e => {
    e.preventDefault();
    // POST to intake_bulk
    await fetch('/agent/intake_bulk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        responses: answers
      })
    });
    setStep('done');
  }

  const fetchRecommendation = async () => {
    const res = await fetch('/agent/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    });
    const json = await res.json();
    setRecommendation(json.recommendation);
    setStep('recommend');
  }

  return (
    <div className="container">
      <h1>Agentic Portfolio Advisor</h1>

      {step === 'survey' && (
        <form onSubmit={handleSubmit} className="survey-form">
          {QUESTIONS.map((q, i) => (
            <div className="field" key={i}>
              <label>{q}</label>
              <input
                type="text"
                value={answers[q]}
                onChange={e => handleChange(q, e.target.value)}
                required
              />
            </div>
          ))}
          <button type="submit" className="btn primary">Submit Answers</button>
        </form>
      )}

      {step === 'done' && (
        <div className="actions">
          <p>Your answers have been recorded.</p>
          <button onClick={fetchRecommendation} className="btn primary">
            Get Recommendation
          </button>
        </div>
      )}

      {step === 'recommend' && (
        <div className="recommendation">
          <h2>Advisor Recommendation</h2>
          <div 
            className="markdown-body" 
            dangerouslySetInnerHTML={{ __html: recommendation }}
          />
        </div>
      )}
    </div>
  )
}

export default App
