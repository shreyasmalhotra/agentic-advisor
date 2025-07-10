"""streaming_agent_chat.py
--------------------------
Utility helpers to stream multi-agent responses over Server-Sent Events (SSE).

`create_agent_stream` orchestrates Data-Fetch → Analysis → Optimization → Explainability
agents and yields properly formatted `data:` events that the front-end consumes.

All helper functions are nested purely for scoping.
"""
import json
import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from supabase._sync.client import create_client, Client

# Ensure .env is loaded
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

# module-level logger
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

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
        message_lower = user_message.lower()

        # -------------------------- INTENT ROUTING --------------------------
        router_intent: str | None = None
        router_options: list[str] = []
        intents_list: list[str] = []  # Initialize empty list with explicit type
        try:
            router_agent_inst = agents.get('router')  # Provided by caller
            if router_agent_inst:
                # Add explicit prompt to ensure consistent format
                router_prompt = f"Classify this user request: \"{user_message}\". Return ONLY a JSON object."
                router_raw = router_agent_inst.run(router_prompt)
                logger.info(f"[ROUTER DEBUG] Raw response: {router_raw}")
                logger.info(f"[ROUTER DEBUG] Response type: {type(router_raw)}")
                
                # First try direct JSON parsing
                try:
                    # Convert RunResponse to string if needed
                    if hasattr(router_raw, 'content'):
                        router_str = router_raw.content
                    else:
                        router_str = str(router_raw)
                    
                    # Clean up the string
                    router_str = router_str.strip()
                    if router_str.startswith('```') and router_str.endswith('```'):
                        router_str = router_str[3:-3].strip()
                    if router_str.startswith('json') or router_str.startswith('JSON'):
                        router_str = router_str[4:].strip()
                    
                    logger.info(f"[ROUTER DEBUG] Cleaned string: {router_str}")
                    
                    # Try direct JSON parsing first
                    try:
                        router_data = json.loads(router_str)
                        logger.info(f"[ROUTER DEBUG] Direct JSON parse successful: {router_data}")
                    except json.JSONDecodeError:
                        # If that fails, try to find JSON in the string
                        import re
                        json_match = re.search(r"\{.*\}", router_str, re.DOTALL)
                        if json_match:
                            json_str = json_match.group()
                            logger.info(f"[ROUTER DEBUG] Extracted JSON: {json_str}")
                            router_data = json.loads(json_str)
                            logger.info(f"[ROUTER DEBUG] Parsed data: {router_data}")
                        else:
                            logger.error("[ROUTER DEBUG] No JSON found in response")
                            router_data = {"intent": "clarify"}
                except Exception as e:
                    logger.error(f"[ROUTER DEBUG] JSON parsing error: {e}")
                    router_data = {"intent": "clarify"}
                
                # Extract intent(s)
                if isinstance(router_data, dict):
                    router_intent = router_data.get('intent')
                    # Ensure router_options is always a list of strings
                    raw_options = router_data.get('options', [])
                    router_options = [str(opt) for opt in raw_options] if isinstance(raw_options, list) else []
                    logger.info(f"[ROUTER DEBUG] Extracted intent: {router_intent}")
                    logger.info(f"[ROUTER DEBUG] Extracted options: {router_options}")
                    
                    if 'intents' in router_data and isinstance(router_data['intents'], list):
                        # Ensure we have a list of strings
                        intents_list = [str(i) for i in router_data['intents']]
                        logger.info(f"[ROUTER DEBUG] Found multiple intents: {intents_list}")
                    elif 'intent' in router_data and router_data['intent'] != 'clarify':
                        # Single intent as list
                        intents_list = [str(router_data['intent'])]
                        logger.info(f"[ROUTER DEBUG] Found single intent: {router_data['intent']}")
                    else:
                        # No valid intents
                        intents_list = []
                        logger.info(f"[ROUTER DEBUG] No valid intents found in response: {router_data}")
                else:
                    logger.error(f"[ROUTER DEBUG] Router data is not a dict: {router_data}")
                    router_data = {"intent": "clarify"}
                    router_intent = "clarify"
                    intents_list = []

                # Log the final decision
                logger.info(f"[ROUTER DEBUG] Final decision for '{user_message}': intent={router_intent}, intents={intents_list}")

        except Exception as e:
            logger.error(f"[ROUTER DEBUG] Router agent failed: {e}")
            router_intent = "clarify"  # Default to clarify on error
            router_data = {"intent": "clarify"}
            intents_list = []

        # ------------------------------------------------------------
        # Helper to run one agent with nice thinking steps.
        # ------------------------------------------------------------
        async def _run_single_agent(agent_key: str, intro: str, think_steps: list[str]):
            yield create_stream_message('agent_start', agent_key, intro)
            await asyncio.sleep(0.4)
            for step in think_steps:
                yield create_stream_message('agent_thinking', agent_key, step)
                await asyncio.sleep(0.4)
            result_raw = agents[agent_key].run(f"Session ID: {session_id}. User request: {user_message}")
            clean_result = extract_clean_content(result_raw)
            yield create_stream_message('agent_result', agent_key, clean_result)

        # If router returns a valid intent, SKIP the legacy trigger routing entirely
        if router_intent and router_intent not in ['clarify', 'unknown', None]:
            # FETCH DATA - Direct and focused
            if router_intent == 'fetch_data':
                yield create_stream_message('agent_start', 'data_fetch', 
                    '🔍 **Data-Fetch Agent**: Retrieving your current portfolio data...')
                await asyncio.sleep(0.4)
                
                yield create_stream_message('agent_thinking', 'data_fetch', 
                    '• Accessing your portfolio information...')
                await asyncio.sleep(0.4)
                
                data_result = agents['data_fetch'].run(f"Session ID: {session_id}. Fetch current portfolio data.")
                yield create_stream_message('agent_response', 'data_fetch', str(data_result))
                
            # ANALYZE DRIFT - Quick and focused
            elif router_intent == 'analyze_drift':
                # First get fresh data
                yield create_stream_message('agent_start', 'data_fetch', 
                    '🔍 **Data-Fetch Agent**: First, let me get your latest portfolio data...')
                await asyncio.sleep(0.4)
                
                data_result = agents['data_fetch'].run(f"Session ID: {session_id}. Quick data refresh for drift analysis.")
                
                # Then analyze drift
                yield create_stream_message('agent_start', 'analysis', 
                    '📊 **Analysis Agent**: Analyzing your portfolio drift...')
                await asyncio.sleep(0.4)
                
                analysis_result = agents['analysis'].run(f"Session ID: {session_id}. Analyze drift in portfolio.")
                yield create_stream_message('agent_response', 'analysis', str(analysis_result))
                
            # OPTIMIZE PORTFOLIO - Streamlined
            elif router_intent == 'optimize_portfolio' or 'optimize my allocation' in message_lower:
                # First, fetch fresh data but with a more focused message
                yield create_stream_message('agent_start', 'data_fetch', 
                    '🔍 **Data-Fetch Agent**: First, let me get your latest portfolio data for optimization...')
                await asyncio.sleep(0.4)
                
                yield create_stream_message('agent_thinking', 'data_fetch', 
                    '• Refreshing your portfolio data...')
                await asyncio.sleep(0.4)
                
                data_result = agents['data_fetch'].run(f"Session ID: {session_id}. Quick data refresh for optimization.")
                
                # Get questionnaire data for optimization context
                try:
                    resp = (
                        supabase
                        .from_("portfolio_sessions")
                        .select("questionnaire_responses")
                        .eq("session_id", session_id)
                        .single()
                        .execute()
                    )
                    q_data = resp.data.get("questionnaire_responses", {}) if resp.data else {}
                    risk_ctx = q_data.get("risk_tolerance", "")
                    goal_ctx = q_data.get("investment_goal", "")
                    horizon_ctx = q_data.get("time_horizon", "")
                    
                    logger.info(f"Fetched questionnaire data: risk={risk_ctx}, goal={goal_ctx}, horizon={horizon_ctx}")
                    
                    if not risk_ctx or not goal_ctx or not horizon_ctx:
                        yield create_stream_message('error', 'optimization',
                            "❌ I couldn't find your questionnaire responses. Please complete the questionnaire first so I know your risk tolerance and goals.")
                        return
                        
                except Exception as e:
                    logger.error(f"Error handling questionnaire data: {e}")
                    yield create_stream_message('error', 'optimization',
                        "❌ I had trouble accessing your questionnaire data. Please try again or complete the questionnaire if you haven't already.")
                    return
                
                # Run optimization agent with questionnaire data
                yield create_stream_message('agent_start', 'optimization', 
                    f'⚙️ **Optimization Agent**: Optimizing your portfolio based on your profile:\n'
                    f'• Risk Tolerance: {risk_ctx}\n'
                    f'• Investment Goal: {goal_ctx}\n'
                    f'• Time Horizon: {horizon_ctx}')
                await asyncio.sleep(0.4)
                
                opt_result = agents['optimization'].run(
                    f"Call optimize_portfolio with:\n"
                    f"1. session_id='{session_id}'\n"
                    f"2. risk_tolerance='{risk_ctx}'\n"
                    f"3. investment_goal='{goal_ctx}'\n"
                    f"4. time_horizon='{horizon_ctx}'\n\n"
                    f"Current portfolio data has been fetched and analyzed. Please provide optimized allocation and specific trade recommendations."
                )
                yield create_stream_message('agent_response', 'optimization', str(opt_result))
                
                # Add explanation
                yield create_stream_message('agent_start', 'explainability', 
                    '💡 **Explainability Agent**: Let me explain these recommendations...')
                await asyncio.sleep(0.4)
                
                explain_result = agents['explainability'].run(
                    f"Explain the optimization results for risk_tolerance='{risk_ctx}' and goal='{goal_ctx}'"
                )
                yield create_stream_message('agent_response', 'explainability', str(explain_result))
                
            # EXPLAIN RECOMMENDATIONS - More focused
            elif router_intent == 'explain_recommendations':
                yield create_stream_message('agent_start', 'explainability', 
                    '💡 **Explainability Agent**: Let me explain the portfolio recommendations...')
                await asyncio.sleep(0.4)
                
                explain_result = agents['explainability'].run(f"Session ID: {session_id}. Explain the latest recommendations.")
                yield create_stream_message('agent_response', 'explainability', str(explain_result))
                
            # FULL ANALYSIS - Complete workflow
            elif router_intent == 'full_analysis':
                # Run the full workflow but with better narration
                yield create_stream_message('agent_start', 'data_fetch', 
                    '🔍 **Starting Full Portfolio Analysis**\n\nFirst, let me gather your current data...')
                await asyncio.sleep(0.4)
                
                data_result = agents['data_fetch'].run(f"Session ID: {session_id}. Fetch current portfolio data.")
                yield create_stream_message('agent_response', 'data_fetch', str(data_result))
                
                yield create_stream_message('agent_start', 'analysis', 
                    '📊 **Analysis Agent**: Now analyzing your portfolio positioning...')
                await asyncio.sleep(0.4)
                
                analysis_result = agents['analysis'].run(f"Session ID: {session_id}. Analyze portfolio drift and risk exposure.")
                yield create_stream_message('agent_response', 'analysis', str(analysis_result))
                
                yield create_stream_message('agent_start', 'optimization', 
                    '⚙️ **Optimization Agent**: Generating optimal allocation...')
                await asyncio.sleep(0.4)
                
                opt_result = agents['optimization'].run(f"Session ID: {session_id}. Optimize portfolio based on analysis.")
                yield create_stream_message('agent_response', 'optimization', str(opt_result))
                
                yield create_stream_message('agent_start', 'explainability', 
                    '💡 **Explainability Agent**: Let me explain these recommendations...')
                await asyncio.sleep(0.4)
                
                explain_result = agents['explainability'].run(f"Session ID: {session_id}. Explain the recommendations.")
                yield create_stream_message('agent_response', 'explainability', str(explain_result))
                
        # CLARIFICATION NEEDED
        elif router_intent == 'clarify':
            # Ask the user for clarification with suggested commands
            options = router_options if router_options else [
                'Show my portfolio data',
                'Analyze my portfolio drift',
                'Optimize my allocation',
                'Explain the recommendations',
                'Run a full portfolio analysis'
            ]
            opts_txt = "\n".join(f"• {opt}" for opt in options)
            yield create_stream_message('agent_response', 'router', 
                "I wasn't completely sure what you wanted. Here are a few things I can do:\n\n" + 
                opts_txt + "\n\nPlease let me know which one you'd like!"
            )
            
        # UNKNOWN INTENT - Fall back to full analysis
        else:
            # Default to full analysis with clear explanation
            yield create_stream_message('agent_response', 'router',
                "I'll run a complete portfolio analysis to help you understand your current situation.\n\n"
                "This will include:\n"
                "• Current portfolio data\n"
                "• Drift analysis\n"
                "• Optimization recommendations\n"
                "• Plain-English explanations\n\n"
                "Starting analysis now..."
            )
            await asyncio.sleep(0.4)
            
            # Run data fetch
            yield create_stream_message('agent_start', 'data_fetch', 
                '🔍 **Data-Fetch Agent**: First, let me gather your current portfolio data...')
            await asyncio.sleep(0.4)
            
            data_result = agents['data_fetch'].run(f"Session ID: {session_id}. Fetch current portfolio data.")
            yield create_stream_message('agent_response', 'data_fetch', str(data_result))
            
            # Run analysis
            yield create_stream_message('agent_start', 'analysis', 
                '📊 **Analysis Agent**: Now analyzing your portfolio positioning...')
            await asyncio.sleep(0.4)
            
            analysis_result = agents['analysis'].run(f"Session ID: {session_id}. Analyze portfolio drift and risk exposure.")
            yield create_stream_message('agent_response', 'analysis', str(analysis_result))
            
            # Run optimization
            yield create_stream_message('agent_start', 'optimization', 
                '⚙️ **Optimization Agent**: Generating optimal allocation...')
            await asyncio.sleep(0.4)
            
            opt_result = agents['optimization'].run(f"Session ID: {session_id}. Optimize portfolio based on analysis.")
            yield create_stream_message('agent_response', 'optimization', str(opt_result))
            
            # Add explanation
            yield create_stream_message('agent_start', 'explainability', 
                '💡 **Explainability Agent**: Let me explain these recommendations...')
            await asyncio.sleep(0.4)
            
            explain_result = agents['explainability'].run(f"Session ID: {session_id}. Explain the recommendations.")
            yield create_stream_message('agent_response', 'explainability', str(explain_result))

        # Only fall through to legacy routing if router completely failed
        if router_intent in ['clarify', 'unknown', None]:
            # Ask for clarification
            opts = router_options or ['Show portfolio data', 'Analyze drift', 'Optimize allocation', 'Explain recommendations']
            opts_text = '\n'.join(f"• {o}" for o in opts)
            yield create_stream_message('agent_start', 'orchestrator', "🤔 I wasn't sure what you wanted. Here are some things I can help with:\n" + opts_text)
            yield create_stream_message('agent_complete', 'orchestrator', 'Please tell me which one sounds right!')
            import json as _json
            yield f"data: {_json.dumps({'type': 'stream_end'})}\n\n"
            return

        # ------------------------------------
        # Multi-intent custom sequence support
        # ------------------------------------
        if intents_list:
            # If the router explicitly asked for full_analysis, let existing block handle
            if 'full_analysis' in intents_list:
                router_intent = 'full_analysis'
            else:
                # Execute sequence respecting dependencies
                has_data = False
                for intent_item in intents_list:
                    if intent_item in ('analyze_drift', 'optimize_portfolio') and not has_data:
                        # fetch fresh data first
                        async for m in _run_single_agent('data_fetch', '🔍 **Data-Fetch Agent**: Retrieving your latest portfolio data...', ['• Refreshing database records...', '• Pulling live prices...']):
                            yield m
                        has_data = True

                    if intent_item == 'fetch_data':
                        async for m in _run_single_agent('data_fetch', '🔍 **Data-Fetch Agent**: Retrieving your portfolio data and current market prices...', ['• Accessing database...', '• Fetching live prices...']):
                            yield m
                        has_data = True
                    elif intent_item == 'analyze_drift':
                        async for m in _run_single_agent('analysis', '📊 **Analysis Agent**: Analyzing your portfolio drift...', ['• Loading your positions...', '• Calculating drift...']):
                            yield m
                    elif intent_item == 'optimize_portfolio':
                        async for m in _run_single_agent('optimization', '⚙️ **Optimization Agent**: Optimizing your portfolio allocation...', ['• Loading risk preferences...', '• Running optimization...']):
                            yield m
                    elif intent_item == 'explain_recommendations':
                        async for m in _run_single_agent('explainability', '💡 **Explainability Agent**: Explaining the rationale behind the recommendations...', ['• Reviewing prior recommendations...', '• Crafting explanation...']):
                            yield m
                # Finish stream
                import json as _json
                yield create_stream_message('agent_complete', 'orchestrator', '✅ Sequence complete. Let me know what else I can help with!')
                yield f"data: {_json.dumps({'type': 'stream_end'})}\n\n"
                return

        if router_intent in ['fetch_data', 'analyze_drift', 'optimize_portfolio', 'explain_recommendations']:
            # Always refresh data first unless the user explicitly only asked for data
            if router_intent != 'fetch_data':
                async for m in _run_single_agent('data_fetch', '🔍 **Data-Fetch Agent**: Retrieving your latest portfolio data...', ['• Refreshing database records...', '• Pulling live prices...']):
                    yield m

            if router_intent == 'fetch_data':
                async for m in _run_single_agent('data_fetch', '🔍 **Data-Fetch Agent**: Retrieving your portfolio data and current market prices...', ['• Accessing database...', '• Fetching live prices...']):
                    yield m
            elif router_intent == 'analyze_drift':
                async for m in _run_single_agent('analysis', '📊 **Analysis Agent**: Analyzing your portfolio drift...', ['• Loading your positions...', '• Calculating drift...']):
                    yield m
            elif router_intent == 'optimize_portfolio':
                async for m in _run_single_agent('optimization', '⚙️ **Optimization Agent**: Optimizing your portfolio allocation...', ['• Loading risk preferences...', '• Running optimization...']):
                    yield m
            elif router_intent == 'explain_recommendations':
                async for m in _run_single_agent('explainability', '💡 **Explainability Agent**: Explaining the rationale behind the recommendations...', ['• Reviewing prior recommendations...', '• Crafting explanation...']):
                    yield m

            import json as _json
            yield create_stream_message('agent_complete', 'orchestrator', '✅ Task complete. Let me know what you would like to do next!')
            yield f"data: {_json.dumps({'type': 'stream_end'})}\n\n"
            return

        elif router_intent in ['clarify', 'unknown', None]:
            # Ask for clarification
            opts = router_options or ['Show portfolio data', 'Analyze drift', 'Optimize allocation', 'Explain recommendations']
            opts_text = '\n'.join(f"• {o}" for o in opts)
            yield create_stream_message('agent_start', 'orchestrator', "🤔 I wasn't sure what you wanted. Here are some things I can help with:\n" + opts_text)
            yield create_stream_message('agent_complete', 'orchestrator', 'Please tell me which one sounds right!')
            import json as _json
            yield f"data: {_json.dumps({'type': 'stream_end'})}\n\n"
            return

        # ---------------------- LEGACY TRIGGER ROUTING ----------------------
        # Check for full workflow triggers
        full_workflow_triggers = [
            "start", "begin", "analysis", "full", "complete", "comprehensive",
            "go ahead", "next step", "continue", "proceed", "do next",
            "diversify", "improve", "better performance"
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
            risk_ctx: str = q_data.get("risk_tolerance", "3 - Moderate")
            goal_ctx: str = q_data.get("investment_goal", "Growth")
            horizon_ctx: str = q_data.get("time_horizon", "5+ years")
        except Exception:
            # Fallback defaults if anything goes wrong
            risk_ctx = "3 - Moderate"
            goal_ctx = "Growth"
            horizon_ctx = "5+ years"

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
                f"Call optimize_portfolio with:\n"
                f"1. session_id='{session_id}'\n"
                f"2. risk_tolerance='{risk_ctx}'\n"  # Make sure to pass as string
                f"3. investment_goal='{goal_ctx}'\n"
                f"4. time_horizon='{horizon_ctx}'\n\n"
                f"Current portfolio data has been fetched and analyzed. Please provide optimized allocation and specific trade recommendations."
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
                f"Risk tolerance: {risk_ctx}. "
                f"Investment goal: {goal_ctx}. "
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