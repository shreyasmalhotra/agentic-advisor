# app.py

import os
from dotenv import load_dotenv
from pathlib import Path

# Ensure .env is located relative to this file so uvicorn can find it even when
# started from a different working directory (e.g. reload subprocess).
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from supabase._sync.client import create_client, Client
from datetime import datetime
import json
import asyncio
import openai
import yfinance as yf
from streaming_agent_chat import create_agent_stream

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Agno imports
from agno.tools import tool
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# 1) Configure OpenAI
openai.api_key = os.environ["OPENAI_API_KEY"]

# 2) Load Supabase credentials
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# 3) Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 4) Application configuration
# Questions are now handled by the frontend questionnaire form

# 5) Database helper functions
def create_new_session(session_id: str) -> dict:
    """Create a new portfolio session in the database"""
    try:
        result = supabase.from_("portfolio_sessions").insert({
            "session_id": session_id,
            "status": "questionnaire_started",
            "questionnaire_responses": {},
            "metadata": {"user_agent": "web", "platform": "agentic_advisor"}
        }).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        print(f"Error creating session: {e}")
        return {}

def get_session(session_id: str) -> dict:
    """Get session data from database"""
    try:
        result = supabase.from_("portfolio_sessions").select("*").eq("session_id", session_id).single().execute()
        return result.data if result.data else {}
    except Exception as e:
        print(f"Error getting session: {e}")
        return {}

def update_session_responses(session_id: str, responses: dict) -> bool:
    """Update questionnaire responses for a session"""
    try:
        supabase.from_("portfolio_sessions").update({
            "questionnaire_responses": responses,
            "status": "questionnaire_completed",
            "completed_at": datetime.utcnow().isoformat()
        }).eq("session_id", session_id).execute()
        return True
    except Exception as e:
        print(f"Error updating session responses: {e}")
        return False

def save_chat_message(session_id: str, message_type: str, content: str, metadata: dict | None = None) -> bool:
    """Save a chat message to the database"""
    try:
        supabase.from_("chat_messages").insert({
            "session_id": session_id,
            "message_type": message_type,
            "content": content,
            "metadata": metadata if metadata is not None else {}
        }).execute()
        return True
    except Exception as e:
        print(f"Error saving chat message: {e}")
        return False

# 7) Expose persistence as an Agno tool (future use)
@tool(name="supabase_db", show_result=True)
def supabase_db_tool(session_id: str, question: str, answer: str) -> str:
    save_chat_message(session_id, "system", f"Saved: {question} → {answer}")
    return "✅ saved"

# 8) Enhanced tools for portfolio analysis
@tool(name="fetch_portfolio_data", show_result=True)
def fetch_portfolio_data(session_id: str, holdings: str) -> str:
    """Fetch live prices for current portfolio holdings.

    Enhanced: If the questionnaire stored a `positions` JSON payload (array of rows
    with ticker / amount / units), we ignore the free-form `holdings` string and
    use that structured data instead.  Fallback to legacy parsing otherwise.
    """
    try:
        # 1) Check DB for structured positions
        try:
            resp = (
                supabase
                .from_("portfolio_sessions")
                .select("questionnaire_responses")
                .eq("session_id", session_id)
                .single()
                .execute()
            )
            raw_q = resp.data.get("questionnaire_responses", {}) if resp.data else {}
            positions_json = raw_q.get("positions")  # this is a JSON-string
            structured_positions = json.loads(positions_json) if positions_json else {}
        except Exception as e:
            structured_positions = {}
            logger.debug("Could not load structured positions: %s", e)

        # Default legacy lookup (empty). Defined early to satisfy linters even though
        # the legacy code path has been removed.
        shares_lookup_legacy: dict[str, float] = {}

        # If we have structured positions, we build ticker list & share counts from it
        if structured_positions:
            tickers: list[str] = []
            shares_lookup: dict[str, float] = {}
            cash_positions: list[str] = []
            position_details: list[str] = []

            for asset_class, rows in structured_positions.items():
                for row in rows:
                    ticker = row.get("ticker", "").upper()
                    if not ticker:
                        continue
                    amount = float(row.get("amount", 0)) if row.get("amount") else 0.0
                    units = row.get("units", "shares")
                    tickers.append(ticker)
                    if units == "shares":
                        shares_lookup[ticker] = shares_lookup.get(ticker, 0) + amount
                    else:  # usd
                        # store negative value to mark as fixed usd value
                        shares_lookup[ticker] = shares_lookup.get(ticker, 0) - amount  # negative means USD
                    position_details.append(f"{ticker}: {asset_class}")
        else:
            # No structured position data – return a clear error instead of guessing.
            return (
                "❌ No detailed position data found. "
                "Please reopen the questionnaire, fill in your holdings table, "
                "and resubmit."
            )
        
        # Remove duplicates while preserving order
        tickers = list(dict.fromkeys(tickers))
        
        # If no tickers found, use smart mapping based on holdings description
        if not tickers:
            holdings_lower = holdings.lower().strip()
            logger.debug("No tickers found, checking holdings_lower: '%s'", holdings_lower)
            
            # Handle predefined multiple choice options from questionnaire
            if 'us equity' in holdings_lower and 's&p 500' in holdings_lower:
                tickers = ['SPY', 'VOO', 'IVV']  # S&P 500 ETFs
                position_details = ['SPY: SPDR S&P 500 ETF', 'VOO: Vanguard S&P 500 ETF', 'IVV: iShares S&P 500 ETF']
                logger.debug("Mapped to S&P 500 ETFs: %s", tickers)
            
            elif 'technology focused' in holdings_lower or 'nasdaq' in holdings_lower or 'tech stocks' in holdings_lower:
                tickers = ['QQQ', 'XLK', 'VGT']  # Technology focused
                position_details = ['QQQ: Nasdaq 100 ETF', 'XLK: Technology Sector ETF', 'VGT: Vanguard Technology ETF']
                logger.debug("Mapped to technology ETFs: %s", tickers)
            
            elif 'diversified us market' in holdings_lower or 'total stock market' in holdings_lower:
                tickers = ['VTI', 'ITOT', 'SPTM']  # Total stock market
                position_details = ['VTI: Vanguard Total Stock Market', 'ITOT: iShares Total Stock Market', 'SPTM: SPDR Total Stock Market']
                logger.debug("Mapped to total market ETFs: %s", tickers)
            
            elif 'international equity' in holdings_lower or 'developed markets' in holdings_lower:
                tickers = ['VEA', 'IEFA', 'SCHF']  # Developed markets
                position_details = ['VEA: Vanguard Developed Markets', 'IEFA: iShares MSCI EAFE', 'SCHF: Schwab International Equity']
                logger.debug("Mapped to international developed markets: %s", tickers)
            
            elif 'emerging markets' in holdings_lower:
                tickers = ['VWO', 'IEMG', 'SCHE']  # Emerging markets
                position_details = ['VWO: Vanguard Emerging Markets', 'IEMG: iShares Emerging Markets', 'SCHE: Schwab Emerging Markets']
                logger.debug("Mapped to emerging markets: %s", tickers)
            
            elif 'bond portfolio' in holdings_lower or 'government' in holdings_lower or 'corporate' in holdings_lower:
                tickers = ['BND', 'AGG', 'TLT']  # Bond portfolio
                position_details = ['BND: Vanguard Total Bond Market', 'AGG: iShares Aggregate Bond', 'TLT: 20+ Year Treasury']
                logger.debug("Mapped to bond portfolio: %s", tickers)
            
            elif 'balanced portfolio' in holdings_lower or 'stocks' in holdings_lower and 'bonds' in holdings_lower:
                tickers = ['VTI', 'BND', 'VXUS']  # Balanced portfolio
                position_details = ['VTI: US Total Stock Market', 'BND: Total Bond Market', 'VXUS: International Stock Market']
                logger.debug("Mapped to balanced portfolio: %s", tickers)
            
            elif 'real estate' in holdings_lower or 'reits' in holdings_lower:
                tickers = ['VNQ', 'SCHH', 'IYR']  # Real estate
                position_details = ['VNQ: Vanguard Real Estate ETF', 'SCHH: Schwab Real Estate ETF', 'IYR: iShares Real Estate ETF']
                logger.debug("Mapped to real estate ETFs: %s", tickers)
            
            elif 'mixed portfolio' in holdings_lower or 'multiple asset classes' in holdings_lower:
                tickers = ['VTI', 'BND', 'VEA', 'VWO']  # Mixed portfolio
                position_details = ['VTI: US Total Stock Market', 'BND: Total Bond Market', 'VEA: Developed Markets', 'VWO: Emerging Markets']
                logger.debug("Mapped to mixed portfolio: %s", tickers)
            
            # Legacy support for older format inputs
            elif (holdings_lower in ['us', 'usa', 'united states'] or 
                'us equity' in holdings_lower or 'us stock' in holdings_lower or 
                'american' in holdings_lower or 'us equities' in holdings_lower or
                'equity' in holdings_lower):  # Default equity to US equity
                tickers = ['SPY', 'QQQ', 'IWM']  # Large cap, tech, small cap
                position_details = ['SPY: S&P 500 ETF', 'QQQ: Nasdaq 100 ETF', 'IWM: Small Cap ETF']
                logger.debug("Mapped to US equities (legacy): %s", tickers)
            
            # Default fallback - assume US equity (most common)
            else:
                tickers = ['SPY', 'QQQ', 'IWM']  # Default to US equities
                position_details = ['SPY: S&P 500 ETF (Default)', 'QQQ: Nasdaq 100 ETF (Default)', 'IWM: Small Cap ETF (Default)']
                logger.debug("Used default US equity portfolio for unknown input: %s", tickers)
        
        # Fetch current prices from Yahoo Finance
        try:
            df = yf.download(tickers, period="5d", progress=False)
            if df is None or df.empty:
                return f"Unable to fetch portfolio data for tickers: {', '.join(tickers)}. Please try again later."
            
            closes = df["Close"]
            latest_prices = closes.iloc[-1] if not closes.empty else {}
            
            # Debug: Print what we got
            logger.debug("Successfully fetched data for tickers: %s", tickers)
            logger.debug("Latest prices: %s", latest_prices)
            
        except Exception as e:
            logger.error("Error fetching data: %s", e)
            return f"Error fetching market data: {str(e)}. Tickers attempted: {', '.join(tickers)}"
        
        # Convert to dict safely
        if hasattr(latest_prices, 'to_dict'):
            price_dict = latest_prices.to_dict()  # type: ignore
        elif isinstance(latest_prices, dict):
            price_dict = latest_prices
        else:
            price_dict = dict(latest_prices) if latest_prices is not None else {}
        
        # Detect tickers with missing prices
        invalid_tickers = [t for t in tickers if t not in price_dict or price_dict[t] is None or (isinstance(price_dict[t], float) and (price_dict[t] != price_dict[t]))]
        if invalid_tickers:
            return (
                "❌ Error: One or more ticker symbols could not be priced: "
                + ", ".join(invalid_tickers)
                + ". Please correct the ticker symbol(s) and resubmit the questionnaire."
            )

        # Calculate portfolio summary
        total_positions = len(tickers) + len(cash_positions)
        
        # Format the response with clear success indication
        response = f"📊 **Portfolio Data Retrieved Successfully:**\n\n"
        response += f"**Live Market Data ({len(tickers)} securities):**\n"
        
        for ticker, price in price_dict.items():
            # Find the description for this ticker
            description = next((detail for detail in position_details if detail.startswith(ticker)), ticker)
            response += f"• **{ticker}**: ${price:.2f} - {description.split(': ', 1)[-1]}\n"
        
        if cash_positions:
            response += f"\n**Cash Positions ({len(cash_positions)}):**\n"
            for cash_pos in cash_positions:
                response += f"• {cash_pos}\n"
        
        response += f"\n**Summary:**\n"
        response += f"• Successfully fetched {len(price_dict)} securities\n"
        response += f"• Input processed: '{holdings}'\n"
        response += f"• Mapped to tickers: {', '.join(tickers)}\n"
        response += f"• Data Status: ✅ Live market prices retrieved from Yahoo Finance\n"
        
        # After latest_prices obtained
        portfolio_lines = []
        total_value = 0.0
        for ticker in tickers:
            price = latest_prices.get(ticker)
            if price is None or (isinstance(price, float) and (price != price)):
                # skip NaN
                continue
            shares_or_usd = shares_lookup.get(ticker) if structured_positions else shares_lookup_legacy.get(ticker, 0)
            if shares_or_usd is None:
                shares_or_usd = 0
            if shares_or_usd >= 0:  # shares mode
                position_val = shares_or_usd * price
                qty_txt = f"{shares_or_usd:.2f} sh"
            else:  # fixed USD amount
                position_val = -shares_or_usd  # stored negative
                qty_txt = f"${-shares_or_usd:,.2f} USD"
            total_value += position_val
            portfolio_lines.append(f"• **{ticker}**: ${price:.2f} × {qty_txt} = **${position_val:,.2f}**")

        # Handle any USD-only rows (simple amount entries without tickers)
        if structured_positions:
            for asset_cls, rows in structured_positions.items():
                for row in rows:
                    if row.get("units") == "usd":
                        amt = float(row.get("amount", 0))
                        if amt <= 0:
                            continue
                        total_value += amt
                        portfolio_lines.append(f"• **{asset_cls}**: ${amt:,.2f} (self-reported)")

        response = f"📊 **Portfolio Data Retrieved Successfully:**\n\n"
        response += "\n".join(portfolio_lines)
        response += f"\n\n**Total Portfolio Market Value:** ${total_value:,.2f}\n"
        response += f"• Data pulled {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} from Yahoo Finance\n"
        return response
        
    except Exception as e:
        return f"Error fetching portfolio data: {str(e)}"

@tool(name="analyze_portfolio_drift", show_result=True)
def analyze_portfolio_drift(session_id: str, risk_tolerance: str) -> str:
    """Compute current equity / bond / cash weights from positions JSON and compare to target mix implied by risk tolerance (1-5)."""
    try:
        risk_level = int(risk_tolerance.split()[0]) if risk_tolerance and risk_tolerance[0].isdigit() else 3

        # Pull structured positions from DB
        resp = (
            supabase
            .from_("portfolio_sessions")
            .select("questionnaire_responses")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        resp_rows = resp.data if isinstance(resp.data, list) else []
        resp_data_raw = resp_rows[0] if resp_rows else {}
        resp_data = resp_data_raw if isinstance(resp_data_raw, dict) else {}
        q = resp_data.get("questionnaire_responses", {}) if resp_data else {}
        positions_json = q.get("positions")
        if not positions_json:
            return "❌ No detailed position data found; please complete the questionnaire first."
        positions = json.loads(positions_json)

        ticker_rows = [row for arr in positions.values() for row in arr]
        if not ticker_rows:
            return "❌ No positions provided."

        tickers = list({row["ticker"].upper() for row in ticker_rows})
        # Fetch prices (5d to reuse cache if possible)
        import pandas as pd  # type: ignore
        df = yf.download(tickers, period="5d", progress=False)
        if df is None or isinstance(df, pd.Series) or df.empty:
            return "❌ Unable to fetch market data for drift analysis."
        if "Close" in df.columns:
            closes = df["Close"]
            latest_prices = closes.iloc[-1].to_dict()
        else:
            # single-ticker returns a Series per column level 0
            latest_prices = {tickers[0]: float(df.iloc[-1])}

        # ------------------------------------------------------------------
        #  Granular bucket calculation – similar to professional SAA models
        #  Buckets: US Eq, Intl Eq, EM Eq, Bonds, RealEstate, Cash
        # ------------------------------------------------------------------
        buckets = {
            'US Equity': 0.0,
            'International Equity': 0.0,
            'Emerging Markets': 0.0,
            'Bonds': 0.0,
            'Real Estate': 0.0,
            'Cash': 0.0,
        }

        def classify(asset_name: str) -> str:
            al = asset_name.lower()
            if 'bond' in al or 'fixed income' in al:
                return 'Bonds'
            if 'real estate' in al or 'reit' in al:
                return 'Real Estate'
            if 'emerging' in al:
                return 'Emerging Markets'
            if 'international' in al or 'developed' in al:
                return 'International Equity'
            if 'cash' in al or 'usd' in al:
                return 'Cash'
            # default
            return 'US Equity'

        for asset_cls, rows in positions.items():
            bucket = classify(asset_cls)
            for row in rows:
                units = row.get("units", "shares")
                amt = float(row.get("amount", 0))
                if units == "usd":
                    position_val = amt
                else:
                    tkr = row.get("ticker", "").upper()
                    price = latest_prices.get(tkr)
                    if price is None or price != price:
                        continue
                    position_val = amt * price
                # Special case: Balanced Portfolio – split 60/40
                if 'balanced' in asset_cls.lower():
                    buckets['US Equity'] += position_val * 0.6
                    buckets['Bonds'] += position_val * 0.4
                else:
                    buckets[bucket] += position_val

        total_val = sum(buckets.values())
        if total_val == 0:
            return "❌ Unable to compute drift — total portfolio value is zero."

        # Convert to % weights
        pct = {k: (v / total_val * 100) for k, v in buckets.items()}

        # Professional style strategic asset-allocation targets by risk band
        target_map_full = {
            1: {'US Equity': 20, 'International Equity': 5, 'Emerging Markets': 0, 'Bonds': 55, 'Real Estate': 5, 'Cash': 15},
            2: {'US Equity': 30, 'International Equity': 10, 'Emerging Markets': 0, 'Bonds': 45, 'Real Estate': 5, 'Cash': 10},
            3: {'US Equity': 40, 'International Equity': 12, 'Emerging Markets': 3, 'Bonds': 35, 'Real Estate': 5, 'Cash': 5},
            4: {'US Equity': 50, 'International Equity': 15, 'Emerging Markets': 5, 'Bonds': 25, 'Real Estate': 5, 'Cash': 0},
            5: {'US Equity': 60, 'International Equity': 20, 'Emerging Markets': 10, 'Bonds': 5,  'Real Estate': 5, 'Cash': 0},
        }

        tgt = target_map_full.get(risk_level, target_map_full[3])

        drift_lines = []
        total_abs_drift = 0.0
        for bucket, target_pct in tgt.items():
            actual = pct.get(bucket, 0.0)
            diff = actual - target_pct
            total_abs_drift += abs(diff)
            drift_lines.append(f"• {bucket}: {diff:+.1f}% {'above' if diff>0 else 'below'} target")

        recommendation = "Drift is within acceptable range." if total_abs_drift < 10 else "Rebalancing recommended to realign with targets."

        drift_report = "\n".join(drift_lines)

        return (
            "📈 Portfolio Drift Analysis:\n" +
            drift_report + "\n" +
            f"• Total portfolio drift: {total_abs_drift:.1f}%\n" +
            f"• Recommendation: {recommendation}"
        )
    except Exception as e:
        return f"Error analyzing portfolio drift: {str(e)}"

@tool(name="optimize_portfolio", show_result=True)
def optimize_portfolio(session_id: str, risk_tolerance: str, investment_goal: str, time_horizon: str) -> str:
    """Generate target allocation & concrete trade tilts based on current bucket weights vs strategic targets."""
    try:
        risk_level = int(risk_tolerance.split()[0]) if risk_tolerance and risk_tolerance[0].isdigit() else 3

        # Load positions JSON
        resp = (
            supabase
            .from_("portfolio_sessions")
            .select("questionnaire_responses")
            .eq("session_id", session_id)
            .limit(1)
            .execute()
        )
        q = resp.data[0]["questionnaire_responses"] if resp.data else {}
        positions_json = q.get("positions")
        if not positions_json:
            return "❌ No position data found; cannot optimize."
        positions = json.loads(positions_json)

        # Build buckets (same helper as drift)
        buckets = {
            'US Equity': 0.0,
            'International Equity': 0.0,
            'Emerging Markets': 0.0,
            'Bonds': 0.0,
            'Real Estate': 0.0,
            'Cash': 0.0,
        }

        def classify(asset_name: str) -> str:
            al = asset_name.lower()
            if 'bond' in al: return 'Bonds'
            if 'real estate' in al or 'reit' in al: return 'Real Estate'
            if 'emerging' in al: return 'Emerging Markets'
            if 'international' in al or 'developed' in al: return 'International Equity'
            if 'cash' in al: return 'Cash'
            return 'US Equity'

        # latest prices (reuse 1-day for speed)
        tickers = list({row['ticker'].upper() for arr in positions.values() for row in arr if row['units']=='shares'})
        import pandas as pd  # type: ignore
        prices: dict[str, float] = {}
        if tickers:
            df = yf.download(tickers, period="1d", progress=False)
            if df is not None and not isinstance(df, pd.Series) and not df.empty and 'Close' in df.columns:
                prices = df['Close'].iloc[-1].to_dict()
            elif tickers:
                prices = {tickers[0]: float(df.iloc[-1])} if isinstance(df, pd.Series) else {}

        for asset_cls, rows in positions.items():
            bucket = classify(asset_cls)
            for row in rows:
                units = row.get('units','shares')
                amt = float(row.get('amount',0))
                val = amt if units=='usd' else amt * prices.get(row['ticker'].upper(),0)
                # balanced split
                if 'balanced' in asset_cls.lower():
                    buckets['US Equity'] += val * 0.6
                    buckets['Bonds'] += val * 0.4
                else:
                    buckets[bucket] += val

        total_val = sum(buckets.values())
        if total_val==0:
            return "❌ Unable to value portfolio; cannot optimize."

        weights = {k: v/total_val*100 for k,v in buckets.items()}

        target_map = {
            1: {'US Equity':20,'International Equity':5,'Emerging Markets':0,'Bonds':55,'Real Estate':5,'Cash':15},
            2: {'US Equity':30,'International Equity':10,'Emerging Markets':0,'Bonds':45,'Real Estate':5,'Cash':10},
            3: {'US Equity':40,'International Equity':12,'Emerging Markets':3,'Bonds':35,'Real Estate':5,'Cash':5},
            4: {'US Equity':50,'International Equity':15,'Emerging Markets':5,'Bonds':25,'Real Estate':5,'Cash':0},
            5: {'US Equity':60,'International Equity':20,'Emerging Markets':10,'Bonds':5,'Real Estate':5,'Cash':0},
        }
        target = target_map.get(risk_level,target_map[3])

        # Build trade directives
        trade_lines = []
        for bucket, tgt in target.items():
            cur = weights.get(bucket,0)
            diff = round(tgt - cur,1)
            if abs(diff)<1: continue  # ignore <1%
            action = 'Buy' if diff>0 else 'Sell'
            trade_lines.append(f"{action} {abs(diff):.1f}% in {bucket}")

        alloc_lines = [f"• {k}: {v}%" for k,v in target.items()]
        trades = "\n".join([f"• {l}" for l in trade_lines]) if trade_lines else "• Portfolio already aligned with target weights."

        return (
            "🎯 Optimized Portfolio Allocation:\n" +
            "\n".join(alloc_lines) + "\n\n" +
            "📋 Suggested Trades:\n" + trades
        )
    except Exception as e:
        return f"Error optimizing portfolio: {str(e)}"

@tool(name="explain_recommendations", show_result=True)
def explain_recommendations(optimization_result: str, risk_tolerance: str, investment_goal: str) -> str:
    """Provide plain-English explanations for portfolio recommendations"""
    try:
        risk_level = int(risk_tolerance.split()[0]) if risk_tolerance and risk_tolerance[0].isdigit() else 3
        
        explanations = []
        
        if risk_level <= 2:
            explanations.append("Given your conservative risk profile, I'm recommending a higher bond allocation to preserve capital while providing steady income.")
        elif risk_level >= 4:
            explanations.append("With your aggressive risk tolerance, I'm suggesting higher equity exposure to maximize long-term growth potential.")
        else:
            explanations.append("For your moderate risk profile, I'm balancing growth and stability with a diversified allocation.")
        
        if 'growth' in investment_goal.lower():
            explanations.append("Since growth is your primary goal, I'm tilting toward equities while maintaining appropriate diversification.")
        elif 'income' in investment_goal.lower():
            explanations.append("To support your income goal, I'm increasing fixed-income allocations that provide regular distributions.")
        elif 'preservation' in investment_goal.lower():
            explanations.append("For capital preservation, I'm emphasizing lower-volatility assets while maintaining some growth exposure.")
        
        explanations.append("The rebalancing will help maintain your target risk level and optimize expected returns within your comfort zone.")
        
        return f"💡 Why These Recommendations Make Sense:\n\n" + \
               f"• {explanations[0]}\n\n" + \
               f"• {explanations[1]}\n\n" + \
               f"• {explanations[2]}\n\n" + \
               f"This strategy aligns with your stated preferences while following modern portfolio theory principles."
        
    except Exception as e:
        return f"Error explaining recommendations: {str(e)}"

# 9) Fetch‐all‐answers tool (for recommender)
@tool(name="supabase_fetch", show_result=False)
def supabase_fetch(session_id: str) -> dict:
    resp = (
        supabase
        .from_("portfolio_sessions")
        .select("questionnaire_responses")
        .eq("session_id", session_id)
        .single()
        .execute()
    )
    if resp.data and isinstance(resp.data.get("questionnaire_responses"), dict):
        return resp.data["questionnaire_responses"]
    return {}

# 10) Multi-Agent Portfolio Rebalancing System

# Data-Fetch Agent
data_fetch_agent = Agent(
    model=OpenAIChat(id="gpt-4-0613", api_key=os.environ["OPENAI_API_KEY"]),
    tools=[supabase_fetch, fetch_portfolio_data],
    instructions=[
        "You are the Data-Fetch Agent for portfolio rebalancing.",
        "Your job is to:",
        "1) Retrieve the user's questionnaire responses using supabase_fetch",
        "2) Extract their current holdings information",
        "3) Fetch live market data for their positions using fetch_portfolio_data",
        "4) Provide a summary of current portfolio state",
        "IMPORTANT: When calling fetch_portfolio_data, pass the FULL holdings description from the questionnaire (e.g., 'US Equity', 'International Stocks', 'Bond Funds') not just abbreviated versions.",
        "CRITICAL: You MUST actually invoke the fetch_portfolio_data tool – do NOT output pseudo-code. Your answer should include the live data returned by the tool call.",
        "Always start with: '🔍 Data-Fetch Agent: I'm now retrieving your portfolio data...'",
        "Narrate what you're doing step by step.",
        "End with a summary of what data you've gathered."
    ],
    markdown=True,
    show_tool_calls=True,
)

# Analysis Agent
analysis_agent = Agent(
    model=OpenAIChat(id="gpt-4-0613", api_key=os.environ["OPENAI_API_KEY"]),
    tools=[supabase_fetch, analyze_portfolio_drift],
    instructions=[
        "You are the Analysis Agent for portfolio rebalancing.",
        "Your job is to:",
        "1) Analyze the portfolio drift from target allocation",
        "2) Identify areas that need rebalancing",
        "3) Ask dynamic follow-up questions if needed (e.g., 'Your tech allocation is high - should I trim it?')",
        "Always start with: '📊 Analysis Agent: I'm analyzing your portfolio drift and risk exposure...'",
        "Provide clear analysis of current vs. target allocations.",
        "Ask for user input on any significant deviations you find."
    ],
    markdown=True,
    show_tool_calls=True,
)

# Optimization Agent
optimization_agent = Agent(
    model=OpenAIChat(id="gpt-4-0613", api_key=os.environ["OPENAI_API_KEY"]),
    tools=[optimize_portfolio],
    instructions=[
        "You are the Optimization Agent for portfolio rebalancing.",
        "Your job is to:",
        "1) Run portfolio optimization based on user's risk profile and goals",
        "2) Generate specific rebalancing recommendations",
        "3) Provide optimal target allocations",
        "Always start with: '⚙️ Optimization Agent: I'm running portfolio optimization algorithms...'",
        "Narrate your optimization process.",
        "Present clear, actionable rebalancing recommendations."
    ],
    markdown=True,
    show_tool_calls=True,
)

# Explainability Agent
explainability_agent = Agent(
    model=OpenAIChat(id="gpt-4-0613", api_key=os.environ["OPENAI_API_KEY"]),
    tools=[explain_recommendations],
    instructions=[
        "You are the Explainability Agent for portfolio rebalancing.",
        "Your job is to:",
        "1) Explain the rationale behind each recommendation in plain English",
        "2) Connect recommendations to the user's specific goals and risk tolerance",
        "3) Make complex financial concepts understandable",
        "Always start with: '💡 Explainability Agent: Let me explain why these recommendations make sense for you...'",
        "Use analogies and simple language when possible.",
        "Always tie explanations back to the user's specific situation."
    ],
    markdown=True,
    show_tool_calls=True,
)

# Orchestrator Agent - Manages the entire workflow
orchestrator_agent = Agent(
    model=OpenAIChat(id="gpt-4-0613", api_key=os.environ["OPENAI_API_KEY"]),
    tools=[supabase_fetch],
    instructions=[
        "You are the Orchestrator Agent for portfolio rebalancing.",
        "You manage the entire multi-agent workflow:",
        "1) Welcome the user and explain the process",
        "2) Coordinate with other agents in sequence: Data-Fetch → Analysis → Optimization → Explainability", 
        "3) Handle dynamic follow-up questions and user interactions",
        "4) Provide a final summary and next steps",
        "Always maintain a professional, helpful tone.",
        "Narrate what's happening at each step so the user understands the process.",
        "Ask for user confirmation before proceeding with major recommendations."
    ],
    markdown=True,
    show_tool_calls=False,
)

# 11) Create FastAPI app
app = FastAPI(title="Agentic Portfolio Advisor")

# Root endpoint - serves a welcome page
@app.get("/")
async def root():
    return {
        "message": "🤖 Agentic Portfolio Advisor API",
        "status": "running",
        "endpoints": {
            "init_session": "POST /init-session - Initialize new portfolio session",
            "submit_questionnaire": "POST /submit-questionnaire - Submit portfolio questionnaire",
            "agent_chat": "POST /agent/chat - Chat with AI portfolio advisor",
            "recommend": "POST /agent/recommend - Get portfolio recommendations"
        },
        "version": "2.0.0"
    }

# 12) Initialize session endpoint
@app.post("/init-session")
async def init_session(request: Request):
    try:
        data = await request.json()
        session_id = data["session_id"]
        
        # Create new session in database
        session = create_new_session(session_id)
        
        if session:
            # Log session initialization
            save_chat_message(
                session_id, 
                "system", 
                "New portfolio advisory session initialized",
                {"user_agent": "web", "platform": "agentic_advisor"}
            )
            
            return {
                "success": True,
                "message": "Session initialized successfully",
                "session_id": session_id
            }
        else:
            return {"success": False, "message": "Failed to initialize session"}
        
    except Exception as e:
        print(f"Error initializing session: {e}")
        return {"success": False, "message": f"Failed to initialize session: {str(e)}"}

# 13) Streaming agent chat endpoint - Real-time agent narration
@app.post("/agent/chat/stream")
async def agent_chat_stream(request: Request):
    """Stream agent responses with real-time narration"""
    try:
        data = await request.json()
        session_id = data["session_id"]
        user_message = data["user_message"]
        
        # Save user message to database
        save_chat_message(session_id, "user", user_message)
        
        # Create agents dictionary for streaming function
        agents = {
            'data_fetch': data_fetch_agent,
            'analysis': analysis_agent,
            'optimization': optimization_agent,
            'explainability': explainability_agent
        }
        
        return StreamingResponse(
            create_agent_stream(session_id, user_message, agents),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        print(f"Error in agent_chat_stream: {e}")
        return {"error": f"Failed to start streaming: {str(e)}"}

# 14) Legacy agent chat endpoint (non-streaming)
@app.post("/agent/chat")
async def agent_chat(request: Request):
    try:
        data = await request.json()
        session_id = data["session_id"]
        user_message = data["user_message"]
        
        # Save user message to database
        save_chat_message(session_id, "user", user_message)
        
        # Get session data for context
        session = get_session(session_id)
        if not session:
            return {"response": "Session not found. Please start a new questionnaire."}
        
        # Determine which agent should handle the request
        if "start analysis" in user_message.lower() or "begin" in user_message.lower():
            # Start the full multi-agent workflow
            try:
                result = orchestrator_agent.run(f"Session ID: {session_id}. User says: {user_message}")
                response = str(result)
            except Exception as e:
                print(f"Error with orchestrator agent: {e}")
                response = "I'm having trouble starting the full analysis right now. Let me try a simpler approach."
        
        elif "data" in user_message.lower() or "portfolio" in user_message.lower():
            # Use data fetch agent
            try:
                result = data_fetch_agent.run(f"Session ID: {session_id}. User request: {user_message}")
                response = str(result)
            except Exception as e:
                print(f"Error with data fetch agent: {e}")
                response = "I'm having trouble fetching your portfolio data right now."
        
        elif "analysis" in user_message.lower() or "drift" in user_message.lower():
            # Use analysis agent
            try:
                result = analysis_agent.run(f"Session ID: {session_id}. User request: {user_message}")
                response = str(result)
            except Exception as e:
                print(f"Error with analysis agent: {e}")
                response = "I'm having trouble analyzing your portfolio right now."
        
        elif "optimize" in user_message.lower() or "recommend" in user_message.lower():
            # Use optimization agent
            try:
                result = optimization_agent.run(f"Session ID: {session_id}. User request: {user_message}")
                response = str(result)
            except Exception as e:
                print(f"Error with optimization agent: {e}")
                response = "I'm having trouble optimizing your portfolio right now."
        
        elif "explain" in user_message.lower() or "why" in user_message.lower():
            # Use explainability agent
            try:
                result = explainability_agent.run(f"Session ID: {session_id}. User request: {user_message}")
                response = str(result)
            except Exception as e:
                print(f"Error with explainability agent: {e}")
                response = "I'm having trouble explaining the recommendations right now."
        
        else:
            # Default to orchestrator for general queries
            try:
                result = orchestrator_agent.run(f"Session ID: {session_id}. User says: {user_message}")
                response = str(result)
            except Exception as e:
                print(f"Error with orchestrator agent: {e}")
                response = """Welcome to your personalized portfolio rebalancing advisor! 

I'm ready to help you optimize your portfolio. I can:

🔍 **Analyze your current holdings** and fetch live market data
📊 **Calculate portfolio drift** from your target allocation  
⚙️ **Optimize your allocation** based on your risk tolerance and goals
💡 **Explain recommendations** in plain English

To get started, just say **"Start my portfolio analysis"** or ask me about any specific aspect of your portfolio."""
        
        # Save agent response to database
        save_chat_message(session_id, "agent", response)
        
        return {"response": response}
        
    except Exception as e:
        print(f"Error in agent_chat: {e}")
        save_chat_message(session_id, "system", f"Error occurred: {str(e)}")
        return {"response": "I apologize, but I'm experiencing technical difficulties. Please try again."}

# 14) Form submission endpoint
@app.post("/submit-questionnaire")
async def submit_questionnaire(request: Request):
    try:
        data = await request.json()
        session_id = data["session_id"]
        responses = data["responses"]
        
        # Check if session exists, if not create it
        existing_session = get_session(session_id)
        if not existing_session:
            create_new_session(session_id)
        
        # Save questionnaire responses to Supabase
        success = update_session_responses(session_id, responses)
        
        if success:
            # Log the questionnaire completion
            save_chat_message(
                session_id, 
                "system", 
                "Questionnaire completed successfully",
                {"responses_count": len(responses), "timestamp": datetime.utcnow().isoformat()}
            )
            
            return {
                "success": True,
                "message": "Questionnaire responses saved successfully",
                "session_id": session_id
            }
        else:
            return {"success": False, "message": "Failed to save responses to database"}
        
    except Exception as e:
        print(f"Error submitting questionnaire: {e}")
        return {"success": False, "message": f"Failed to save responses: {str(e)}"}

# ---------------------------------------------------------------------------
# Compatibility endpoint for the original CRA front-end
# ---------------------------------------------------------------------------
# The restored React app posts the questionnaire answers to `/agent/intake_bulk`.
# This helper simply proxies the request to the existing session-update logic so
# we don’t have to touch the front-end code.


@app.post("/agent/intake_bulk")
async def agent_intake_bulk(request: Request):
    """Accept bulk questionnaire responses from the CRA front-end."""
    try:
        data = await request.json()
        session_id = data["session_id"]
        responses = data["responses"]

        # create session if missing (idempotent)
        if not get_session(session_id):
            create_new_session(session_id)

        ok = update_session_responses(session_id, responses)
        return {"success": ok}
    except Exception as e:
        logger.exception("Error in /agent/intake_bulk: %s", e)
        return {"success": False, "error": str(e)}

# 15) Recommendation endpoint
@app.post("/agent/recommend")
async def agent_recommend(request: Request):
    data       = await request.json()
    session_id = data["session_id"]
    result     = orchestrator_agent.run({"session_id": session_id})
    return {"recommendation": str(result)}

# 11-a) Lightweight ticker-validation endpoint (used by the front-end to flag typos early)
@app.get("/validate-ticker/{ticker}")
async def validate_ticker(ticker: str):
    """Return {valid: bool, price: float|None}.  Uses yfinance.fast_info for speed."""
    import math
    try:
        info = yf.Ticker(ticker.upper()).fast_info  # type: ignore[attr-defined]
        price = info.get("lastPrice") or info.get("last_price")  # yfinance keys vary by version
        if price is None or (isinstance(price, (int, float)) and math.isnan(price)):
            return {"valid": False, "price": None}
        return {"valid": True, "price": float(price)}
    except Exception as e:
        # any exception -> treat as invalid but expose reason for debugging
        return {"valid": False, "error": str(e)}

# Note: React app runs separately on port 3000 in development
