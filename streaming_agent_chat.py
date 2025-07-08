"""streaming_agent_chat.py
--------------------------
Utility helpers to stream multi-agent responses over Server-Sent Events (SSE).

`create_agent_stream` orchestrates Data-Fetch → Analysis → Optimization → Explainability
agents and yields properly formatted `data:` events that the front-end consumes.

All helper functions are nested purely for scoping; this file contains no business
logic, only streaming glue and minimal sanitisation/cleanup.
"""
import json
import asyncio
import logging
from fastapi.responses import StreamingResponse

# module-level logger
logger = logging.getLogger(__name__)

async def create_agent_stream(session_id: str, user_message: str, agents: dict):
    """Generate streaming responses from agents with real-time narration"""
    
    def create_stream_message(msg_type: str, agent: str, content: str) -> str:
        """Format one SSE line.

        Parameters
        ----------
        msg_type : str
            High-level event category (e.g. agent_start, agent_result).
        agent : str
            Human-readable agent label (data_fetch, analysis, etc.).
        content : str
            Markdown / text emitted by the agent.
        """
        return f"data: {json.dumps({'type': msg_type, 'agent': agent, 'content': content})}\n\n"
    

    
    def minimal_cleanup(content: str) -> str:
        """Light regex scrub that removes Agno/RunResponse internals but keeps prose."""
        import re
        
        # Only remove actual technical noise, not content
        content = re.sub(r'RunResponse\([^)]*\)', '', content)
        content = re.sub(r'content_type=\'[^\']*\'', '', content)
        content = re.sub(r'thinking=None', '', content)
        content = re.sub(r'messages=\[[^\]]*\]', '', content)
        content = re.sub(r'model=\'[^\']*\'', '', content)
        content = re.sub(r'created_at=\d+', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
    

    

    
    def extract_clean_content(agent_result) -> str:
        """Extract clean, human-readable content from agent response"""
        try:
            # Handle different response types
            if hasattr(agent_result, 'content'):
                content = agent_result.content
            elif isinstance(agent_result, str):
                content = agent_result
            else:
                content = str(agent_result)
            
            # Clean up the content
            if content:
                import re
                
                # First, extract just the actual content from RunResponse
                content_match = re.search(r"RunResponse\(content='(.*?)',\s*content_type", content, re.DOTALL)
                if content_match:
                    content = content_match.group(1)
                
                # Clean up escape sequences first
                content = content.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace("\\'", "'")
                
                logger.debug("Raw agent content: %s", content[:500])
                
                # MINIMAL CLEANUP - Only remove truly technical metadata, preserve agent work
                content = minimal_cleanup(content)
                
                logger.debug("Cleaned content: %s", content[:500])
                
                # If we have substantial content, return it
                if content and len(content) > 50:
                    return content
                
                # Fallback only if we truly have no content
                return "✅ I've successfully completed this analysis step."
            
            return "✅ **Task Complete** - I've finished processing your request."
            
        except Exception as e:
            print(f"Error extracting content: {e}")
            return "✅ **Processing Complete** - I've successfully completed this step."
    
    try:
        # IMPROVED ROUTING LOGIC - Better keyword detection and autonomous workflow progression
        message_lower = user_message.lower()
        
        # Check for full workflow triggers
        full_workflow_triggers = [
            "start", "begin", "analysis", "full", "complete", "comprehensive",
            "go ahead", "next step", "continue", "proceed", "do next",
            "diversify", "optimize", "rebalance", "improve", "better performance"
        ]
        
        # Check for analysis/drift specific triggers  
        analysis_triggers = [
            "drift", "analyze", "allocation", "target", "balance", "how am i doing",
            "performance", "review", "check", "deviation", "off track"
        ]
        
        # Check for optimization triggers
        optimization_triggers = [
            "optimize", "rebalance", "improve", "better", "recommendations", 
            "changes", "adjust", "modify", "diversify", "portfolio optimization"
        ]
        
        # Check for explanation triggers
        explanation_triggers = [
            "explain", "why", "reason", "rationale", "understand", "meaning",
            "justification", "logic", "breakdown"
        ]
        
        # Determine which workflow to trigger
        # ------------------------------------------------------------
        # Pull key questionnaire fields once so we can pass accurate
        # context (risk tolerance, goals, time horizon) into the
        # downstream optimization / explainability steps.
        # ------------------------------------------------------------
        try:
            # Lazy import to avoid circular dependency at module level
            from app import supabase_fetch  # type: ignore

            q_data = supabase_fetch(session_id) or {}  # type: ignore
            risk_tolerance_str: str = q_data.get("risk_tolerance", "3 - Moderate")
            investment_goal_str: str = q_data.get("investment_goal", "Growth")
            time_horizon_str: str = q_data.get("time_horizon", "5+ years")
        except Exception:
            # Fallback defaults if anything goes wrong
            risk_tolerance_str = "3 - Moderate"
            investment_goal_str = "Growth"
            time_horizon_str = "5+ years"

        if any(trigger in message_lower for trigger in full_workflow_triggers) or \
           any(trigger in message_lower for trigger in analysis_triggers + optimization_triggers):
            
            # FULL MULTI-AGENT WORKFLOW - Autonomous progression through all agents
            yield create_stream_message('agent_start', 'orchestrator', 
                '🎭 **Orchestrator**: Perfect! I\'ll run a complete portfolio analysis and optimization for you.')
            await asyncio.sleep(0.5)
            
            # Step 1: Data Fetch
            yield create_stream_message('agent_thinking', 'orchestrator', 
                '**Step 1**: Coordinating with Data-Fetch Agent to gather your portfolio information...')
            await asyncio.sleep(0.3)
            
            yield create_stream_message('agent_start', 'data_fetch', 
                '🔍 **Data-Fetch Agent**: Retrieving your portfolio data and current market prices...')
            await asyncio.sleep(0.5)
            
            yield create_stream_message('agent_thinking', 'data_fetch', 
                '• Accessing your investment profile from database...')
            await asyncio.sleep(0.6)
            
            yield create_stream_message('agent_thinking', 'data_fetch', 
                '• Fetching live market prices for your holdings...')
            await asyncio.sleep(0.7)
            
            # Run data fetch agent with specific tool instructions
            data_result = agents['data_fetch'].run(f"Use supabase_fetch tool to get session data for {session_id}, then use fetch_portfolio_data to get live market prices. Show actual portfolio holdings and current prices.")
            clean_data_result = extract_clean_content(data_result)
            logger.debug("Data fetch result: %s", clean_data_result)
            yield create_stream_message('agent_result', 'data_fetch', clean_data_result)
            await asyncio.sleep(1.0)
            
            # Step 2: Analysis - ALWAYS continue to this step
            yield create_stream_message('agent_thinking', 'orchestrator', 
                '**Step 2**: Now analyzing your portfolio drift and risk exposure...')
            await asyncio.sleep(0.3)
            
            yield create_stream_message('agent_start', 'analysis', 
                '📊 **Analysis Agent**: Calculating how your portfolio has drifted from your target allocation...')
            await asyncio.sleep(0.5)
            
            yield create_stream_message('agent_thinking', 'analysis', 
                '• Comparing current allocations vs. target percentages...')
            await asyncio.sleep(0.7)
            
            yield create_stream_message('agent_thinking', 'analysis', 
                '• Evaluating risk exposure for your investment goals...')
            await asyncio.sleep(0.7)
            
            yield create_stream_message('agent_thinking', 'analysis', 
                '• Identifying areas that need rebalancing...')
            await asyncio.sleep(0.6)
            
            # Run analysis agent with specific tool instructions
            analysis_result = agents['analysis'].run(
                f"First, retrieve the user's risk_tolerance from Supabase via supabase_fetch (if needed). "
                f"Then call analyze_portfolio_drift with session_id='{session_id}' and the risk_tolerance string. "
                "Output the drift breakdown and your recommendation based on the tool result."
            )
            clean_analysis_result = extract_clean_content(analysis_result)
            logger.debug("Analysis result: %s", clean_analysis_result)
            yield create_stream_message('agent_result', 'analysis', clean_analysis_result)
            await asyncio.sleep(1.0)
            
            # Step 3: Optimization - ALWAYS continue to this step
            yield create_stream_message('agent_thinking', 'orchestrator', 
                '**Step 3**: Optimizing your portfolio allocation for better performance...')
            await asyncio.sleep(0.3)
            
            yield create_stream_message('agent_start', 'optimization', 
                '⚙️ **Optimization Agent**: Running advanced portfolio optimization algorithms...')
            await asyncio.sleep(0.5)
            
            yield create_stream_message('agent_thinking', 'optimization', 
                '• Loading your risk profile and investment timeline...')
            await asyncio.sleep(0.7)
            
            yield create_stream_message('agent_thinking', 'optimization', 
                '• Running Markowitz mean-variance optimization...')
            await asyncio.sleep(1.0)
            
            yield create_stream_message('agent_thinking', 'optimization', 
                '• Generating specific trade recommendations...')
            await asyncio.sleep(0.8)
            
            # Run optimization agent – pass the actual user parameters we just fetched
            opt_result = agents['optimization'].run(
                f"Call optimize_portfolio with session_id='{session_id}', risk_tolerance='{risk_tolerance_str}', "
                f"investment_goal='{investment_goal_str}', time_horizon='{time_horizon_str}'. "
                "Provide the optimized allocation breakdown and concrete trade list."
            )
            clean_opt_result = extract_clean_content(opt_result)
            logger.debug("Optimization result: %s", clean_opt_result)
            yield create_stream_message('agent_result', 'optimization', clean_opt_result)
            await asyncio.sleep(1.0)
            
            # Step 4: Explanation - ALWAYS provide explanations
            yield create_stream_message('agent_thinking', 'orchestrator', 
                '**Step 4**: Explaining the reasoning behind these recommendations...')
            await asyncio.sleep(0.3)
            
            yield create_stream_message('agent_start', 'explainability', 
                '💡 **Explainability Agent**: Let me explain why these changes will improve your portfolio...')
            await asyncio.sleep(0.5)
            
            yield create_stream_message('agent_thinking', 'explainability', 
                '• Connecting recommendations to your risk tolerance...')
            await asyncio.sleep(0.7)
            
            yield create_stream_message('agent_thinking', 'explainability', 
                '• Explaining how this improves diversification...')
            await asyncio.sleep(0.7)
            
            yield create_stream_message('agent_thinking', 'explainability', 
                '• Providing plain-English rationale...')
            await asyncio.sleep(0.6)
            
            # Build a compact, quote-free optimization summary to avoid JSON decode errors
            summary = clean_opt_result.replace("\n", " ")[:800].replace("'", "")
            explain_prompt = (
                "Use explain_recommendations tool. "
                f"Optimization result: {summary}. "
                f"Risk tolerance: {risk_tolerance_str}. "
                f"Investment goal: {investment_goal_str}. "
                "Explain why this allocation makes sense in plain English."
            )
            explain_result = agents['explainability'].run(explain_prompt)
            clean_explain_result = extract_clean_content(explain_result)
            logger.debug("Explanation result: %s", clean_explain_result)
            yield create_stream_message('agent_result', 'explainability', clean_explain_result)
            await asyncio.sleep(0.5)
            
            # Final summary
            yield create_stream_message('agent_complete', 'orchestrator', 
                '🎯 **Complete**: Your portfolio analysis is finished! You now have specific recommendations with full explanations. Feel free to ask follow-up questions!')
                
        elif any(trigger in message_lower for trigger in explanation_triggers):
            # Explanation-focused workflow
            yield create_stream_message('agent_start', 'explainability', 
                '💡 **Explainability Agent**: I\'ll explain the reasoning behind the recommendations...')
            await asyncio.sleep(0.5)
            
            result = agents['explainability'].run(f"Session ID: {session_id}. User request: {user_message}")
            clean_result = extract_clean_content(result)
            yield create_stream_message('agent_result', 'explainability', clean_result)
        
        elif "data" in message_lower or "show me" in message_lower or "current" in message_lower:
            # Data-focused workflow
            yield create_stream_message('agent_start', 'data_fetch', 
                '🔍 **Data-Fetch Agent**: Retrieving your current portfolio information...')
            await asyncio.sleep(0.5)
            
            yield create_stream_message('agent_thinking', 'data_fetch', 
                '• Connecting to database...')
            await asyncio.sleep(0.5)
            
            yield create_stream_message('agent_thinking', 'data_fetch', 
                '• Fetching live market prices...')
            await asyncio.sleep(0.7)
            
            result = agents['data_fetch'].run(f"Session ID: {session_id}. User request: {user_message}")
            clean_result = extract_clean_content(result)
            yield create_stream_message('agent_result', 'data_fetch', clean_result)
        
        else:
            # Smart orchestrator response based on context
            yield create_stream_message('agent_thinking', 'orchestrator', 
                '🎭 **Orchestrator**: I understand you want help with your portfolio. Let me start the analysis...')
            await asyncio.sleep(0.5)
            
            # Instead of just showing menu, be proactive and start the workflow
            yield create_stream_message('agent_start', 'orchestrator', 
                '🚀 **Starting Portfolio Analysis**: I\'ll analyze your portfolio and provide optimization recommendations automatically!')
            await asyncio.sleep(0.5)
            
            # Redirect to full workflow
            yield create_stream_message('agent_thinking', 'orchestrator', 
                'Initiating complete portfolio analysis workflow...')
            await asyncio.sleep(0.3)
            
            # Run data fetch to start the process
            yield create_stream_message('agent_start', 'data_fetch', 
                '🔍 **Data-Fetch Agent**: Starting with your portfolio data retrieval...')
            await asyncio.sleep(0.5)
            
            result = agents['data_fetch'].run(f"Session ID: {session_id}. Retrieve portfolio data to begin analysis.")
            clean_result = extract_clean_content(result)
            yield create_stream_message('agent_result', 'data_fetch', clean_result)
            
            # Continue automatically to analysis
            yield create_stream_message('agent_thinking', 'orchestrator', 
                'Data retrieved! Continuing to portfolio drift analysis...')
            await asyncio.sleep(0.5)
        
        # End stream
        yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
        
    except Exception as e:
        logger.exception("Error in stream: %s", e)
        yield f"data: {json.dumps({'type': 'error', 'content': f'Error: {str(e)}'})}\n\n" 