# Multi-Agent Flow (overview)

1. **Data-Fetch** – grabs questionnaire answers & live market prices.
2. **Analysis** – checks how far each bucket drifts from the target mix.
3. **Optimizer** – suggests buy/sell tilts based on risk score.
4. **Explain** – turns the numbers into plain-English reasoning.

The orchestrator that glues everything together lives in `streaming_agent_chat.py`. 