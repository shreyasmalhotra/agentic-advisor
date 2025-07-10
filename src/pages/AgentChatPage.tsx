import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { MessageCircle, Send, Bot, User, TrendingUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { ClientProfile } from '../App';
import axios from 'axios';

interface AgentChatPageProps {
  clientProfile: ClientProfile;
  responses: Record<string, string>;
  onComplete: () => void;
}

const ChatContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--gray-50);
`;

const Header = styled.header`
  background: var(--white);
  padding: 1.5rem 0;
  box-shadow: var(--shadow-sm);
  border-bottom: 1px solid var(--gray-200);
`;

const HeaderContent = styled.div`
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const HeaderInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const HeaderIcon = styled.div`
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--white);
  box-shadow: 0 2px 8px rgba(26, 54, 93, 0.2);
  
  svg {
    color: var(--white) !important;
  }
`;

const HeaderText = styled.div``;

const HeaderTitle = styled.h1`
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
  color: var(--primary-blue);
  font-weight: 700;
`;

const HeaderSubtitle = styled.p`
  color: #374151;
  margin: 0;
  font-weight: 500;
`;

const StatusBadge = styled.div<{ isActive?: boolean }>`
  background: ${props => props.isActive ? 'var(--primary-blue)' : 'var(--success-green)'};
  color: var(--white) !important;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-lg);
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  
  * {
    color: var(--white) !important;
  }
  
  svg {
    color: var(--white) !important;
  }
  
  ${props => props.isActive && `
    animation: pulse 2s infinite;
    
    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4); }
      70% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
      100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0); }
    }
  `}
`;

const ChatArea = styled.div`
  flex: 1;
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 2rem;
`;

const MessagesContainer = styled.div`
  background: var(--white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 500px;
`;

const MessagesHeader = styled.div`
  padding: 1.5rem;
  border-bottom: 1px solid var(--gray-200);
  background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
  color: var(--white);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  
  h3 {
    color: var(--white);
    margin: 0;
  }
`;

const MessagesTitle = styled.h3`
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const MessagesList = styled.div`
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const Message = styled(motion.div)<{ isAgent?: boolean }>`
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  
  ${props => !props.isAgent && `
    flex-direction: row-reverse;
  `}
`;

const MessageAvatar = styled.div<{ isAgent?: boolean }>`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 600;
  
  ${props => props.isAgent ? `
    background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
    color: var(--white);
    box-shadow: 0 2px 8px rgba(26, 54, 93, 0.2);
  ` : `
    background: #374151;
    color: var(--white);
    box-shadow: 0 2px 8px rgba(55, 65, 81, 0.2);
  `}
`;

const MessageBubble = styled.div<{ isAgent?: boolean; messageType?: string }>`
  max-width: 70%;
  padding: 1rem 1.25rem;
  border-radius: var(--radius-lg);
  
  ${props => {
    if (!props.isAgent) {
      return `
        background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
        color: var(--white);
        border-bottom-right-radius: var(--radius-sm);
        
        strong {
          color: var(--white);
        }
        
        h1, h2, h3, h4, h5, h6 {
          color: var(--white);
        }
        
        * {
          color: var(--white) !important;
        }
      `;
    }
    
    switch (props.messageType) {
      case 'thinking':
        return `
          background: #f8fafc;
          color: #1e293b;
          border-left: 4px solid var(--primary-blue);
          font-style: italic;
          font-size: 0.95rem;
          font-weight: 500;
        `;
      case 'start':
        return `
          background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
          color: var(--white);
          font-weight: 600;
          
          strong {
            color: var(--white);
          }
          
          h1, h2, h3, h4, h5, h6 {
            color: var(--white);
          }
          
          * {
            color: var(--white) !important;
          }
        `;
      case 'result':
        return `
          background: #f0f9ff;
          color: #0c4a6e;
          border-left: 4px solid #0ea5e9;
          font-weight: 500;
        `;
      case 'complete':
        return `
          background: linear-gradient(135deg, #059669 0%, #10b981 100%);
          color: var(--white);
          font-weight: 600;
          
          strong {
            color: var(--white);
          }
          
          h1, h2, h3, h4, h5, h6 {
            color: var(--white);
          }
          
          * {
            color: var(--white) !important;
          }
        `;
      default:
        return `
          background: var(--white);
          color: #1f2937;
          border-bottom-left-radius: var(--radius-sm);
          border: 1px solid #e5e7eb;
        `;
    }
  }}
  
  /* Markdown styling */
  p {
    margin: 0.5rem 0;
    line-height: 1.6;
    
    &:first-child {
      margin-top: 0;
    }
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  strong {
    font-weight: 700;
    color: ${props => {
      if (!props.isAgent) return 'inherit';
      if (props.messageType === 'start' || props.messageType === 'complete') return 'inherit';
      return '#111827';
    }};
  }
  
  h1, h2, h3, h4, h5, h6 {
    color: ${props => {
      if (!props.isAgent) return 'inherit';
      if (props.messageType === 'start' || props.messageType === 'complete') return 'inherit';
      return '#111827';
    }};
    font-weight: 700;
    margin: 1rem 0 0.5rem 0;
    
    &:first-child {
      margin-top: 0;
    }
  }
  
  ul, ol {
    margin: 0.75rem 0;
    padding-left: 1.5rem;
    
    li {
      margin: 0.25rem 0;
      color: ${props => {
        if (!props.isAgent) return 'inherit';
        if (props.messageType === 'start' || props.messageType === 'complete') return 'inherit';
        return '#374151';
      }};
    }
  }
  
  hr {
    margin: 1rem 0;
    border: none;
    border-top: 1px solid ${props => props.isAgent ? '#d1d5db' : 'rgba(255,255,255,0.3)'};
  }
  
  code {
    background: ${props => {
      if (!props.isAgent) return 'rgba(255,255,255,0.2)';
      if (props.messageType === 'start' || props.messageType === 'complete') return 'rgba(255,255,255,0.2)';
      return '#f3f4f6';
    }};
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-size: 0.9em;
    color: ${props => {
      if (!props.isAgent) return 'inherit';
      if (props.messageType === 'start' || props.messageType === 'complete') return 'inherit';
      return '#1f2937';
    }};
  }
`;

const InputArea = styled.div`
  background: var(--white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: 1.5rem;
`;

const InputContainer = styled.div`
  display: flex;
  gap: 1rem;
  align-items: flex-end;
`;

const InputField = styled.textarea`
  flex: 1;
  border: 2px solid #d1d5db;
  border-radius: var(--radius-md);
  padding: 0.75rem;
  font-size: 1rem;
  resize: none;
  min-height: 60px;
  max-height: 150px;
  color: #1f2937;
  background: var(--white);
  
  &::placeholder {
    color: #6b7280;
    font-weight: 400;
  }
  
  &:focus {
    border-color: var(--primary-blue);
    box-shadow: 0 0 0 3px rgba(26, 54, 93, 0.1);
    outline: none;
  }
  
  &:disabled {
    background: #f9fafb;
    color: #9ca3af;
    cursor: not-allowed;
  }
`;

const SendButton = styled(motion.button)<{ disabled?: boolean }>`
  background: ${props => props.disabled ? '#9ca3af' : 'linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%)'};
  color: var(--white);
  padding: 0.75rem;
  border-radius: var(--radius-md);
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  border: none;
  
  svg {
    color: var(--white) !important;
  }
  
  &:hover {
    ${props => !props.disabled && `
      transform: scale(1.05);
      box-shadow: var(--shadow-lg);
    `}
  }
`;

const TypingIndicator = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #374151;
  font-style: italic;
  margin-top: 1rem;
  font-weight: 500;
`;

const TypingDots = styled.div`
  display: flex;
  gap: 4px;
  
  span {
    width: 8px;
    height: 8px;
    background: #6b7280;
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
    
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
  
  @keyframes typing {
    0%, 80%, 100% { opacity: 0.4; transform: scale(0.8); }
    40% { opacity: 1; transform: scale(1); }
  }
`;

interface StreamMessage {
  id: string;
  content: string;
  isAgent: boolean;
  agent?: string;
  type?: 'message' | 'thinking' | 'result' | 'start' | 'complete';
}

const AgentChatPage: React.FC<AgentChatPageProps> = ({ clientProfile, responses, onComplete }) => {
  const [messages, setMessages] = useState<Array<StreamMessage>>([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [activeAgent, setActiveAgent] = useState<string>('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionData, setSessionData] = useState<Record<string, any>>(responses);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Fetch fresh data from Supabase
    const fetchSessionData = async () => {
      try {
        const response = await axios.get(`/agent/session/${clientProfile.sessionId}`);
        if (response.data?.questionnaire_responses) {
          setSessionData(response.data.questionnaire_responses);
        }
      } catch (error) {
        console.error('Error fetching session data:', error);
      }
    };
    
    fetchSessionData();
  }, [clientProfile.sessionId]);

  useEffect(() => {
    // Start with a welcome message from the AI
    const welcomeMessage = {
      id: 'welcome',
      content: `# 🎯 Welcome to your Agentic Portfolio Rebalancing Advisor!

I've received your questionnaire responses and I'm ready to provide personalized portfolio optimization. Based on your **${sessionData.investment_goal}** goal and **${sessionData.risk_tolerance}** risk tolerance, I'll use multiple specialized AI agents to help you.

## Here's how I work:

**🔍 Data-Fetch Agent** - Retrieves your portfolio data and market prices  
**📊 Analysis Agent** - Calculates drift from target allocations  
**⚙️ Optimization Agent** - Runs portfolio optimization algorithms  
**💡 Explainability Agent** - Explains recommendations in plain English  
**🎭 Orchestrator Agent** - Coordinates everything seamlessly

## To get started, try saying:

• **"Start my portfolio analysis"** - Full end-to-end optimization  
• **"Show me my portfolio data"** - Current holdings analysis  
• **"Analyze my drift"** - Portfolio balance review  
• **"Optimize my allocation"** - Get rebalancing recommendations  
• **"Explain why"** - Understand the reasoning

**I'll narrate each step so you can see exactly what I'm doing!** 🚀`,
      isAgent: true
    };
    
    setMessages([welcomeMessage]);
  }, [sessionData]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!currentInput.trim() || isStreaming) return;

    // Add user message
    const userMessage: StreamMessage = {
      id: Date.now().toString(),
      content: currentInput,
      isAgent: false,
      type: 'message'
    };
    
    setMessages(prev => [...prev, userMessage]);
    const inputToSend = currentInput;
    setCurrentInput('');
    setIsStreaming(true);
    setIsTyping(true);

    try {
      // Use Server-Sent Events for streaming
      const response = await fetch('/agent/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: clientProfile.sessionId,
          user_message: inputToSend
        })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (reader) {
        let buffer = '';
        
        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'stream_end') {
                  setIsStreaming(false);
                  setIsTyping(false);
                  setActiveAgent('');
                  break;
                }
                
                if (data.type === 'error') {
                  const errorMessage: StreamMessage = {
                    id: Date.now().toString(),
                    content: data.content,
                    isAgent: true,
                    type: 'message'
                  };
                  setMessages(prev => [...prev, errorMessage]);
                  break;
                }
                
                // Handle different streaming message types
                if (data.type === 'agent_start') {
                  setActiveAgent(data.agent);
                  const agentMessage: StreamMessage = {
                    id: Date.now().toString(),
                    content: data.content,
                    isAgent: true,
                    agent: data.agent,
                    type: 'start'
                  };
                  setMessages(prev => [...prev, agentMessage]);
                }
                
                if (data.type === 'agent_thinking') {
                  const thinkingMessage: StreamMessage = {
                    id: Date.now().toString(),
                    content: data.content,
                    isAgent: true,
                    agent: data.agent,
                    type: 'thinking'
                  };
                  setMessages(prev => [...prev, thinkingMessage]);
                }
                
                if (data.type === 'agent_result') {
                  const resultMessage: StreamMessage = {
                    id: Date.now().toString(),
                    content: data.content,
                    isAgent: true,
                    agent: data.agent,
                    type: 'result'
                  };
                  setMessages(prev => [...prev, resultMessage]);
                }
                
                if (data.type === 'agent_complete') {
                  const completeMessage: StreamMessage = {
                    id: Date.now().toString(),
                    content: data.content,
                    isAgent: true,
                    agent: data.agent,
                    type: 'complete'
                  };
                  setMessages(prev => [...prev, completeMessage]);
                  setActiveAgent('');
                }
              } catch (e) {
                console.error('Error parsing streaming data:', e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Error with streaming:', error);
      const errorResponse: StreamMessage = {
        id: Date.now().toString(),
        content: "I apologize, but I'm experiencing technical difficulties. Please try again.",
        isAgent: true,
        type: 'message'
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsStreaming(false);
      setIsTyping(false);
      setActiveAgent('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <ChatContainer>
      <Header>
        <HeaderContent>
          <HeaderInfo>
            <HeaderIcon>
              <TrendingUp size={24} />
            </HeaderIcon>
            <HeaderText>
              <HeaderTitle>AI Portfolio Advisor</HeaderTitle>
              <HeaderSubtitle>Personalized investment guidance powered by AI</HeaderSubtitle>
            </HeaderText>
          </HeaderInfo>
          
          <StatusBadge isActive={isStreaming}>
            <MessageCircle size={16} />
            {isStreaming 
              ? `${activeAgent.charAt(0).toUpperCase() + activeAgent.slice(1)} Agent Active`
              : 'Ready'
            }
          </StatusBadge>
        </HeaderContent>
      </Header>

      <ChatArea>
        <MessagesContainer>
          <MessagesHeader>
            <MessagesTitle>
              <Bot size={20} />
              Portfolio Advisory Session
            </MessagesTitle>
          </MessagesHeader>
          
          <MessagesList>
            {messages.map((message) => (
              <Message
                key={message.id}
                isAgent={message.isAgent}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <MessageAvatar isAgent={message.isAgent}>
                  {message.isAgent ? <Bot size={20} /> : <User size={20} />}
                </MessageAvatar>
                <MessageBubble 
                  isAgent={message.isAgent}
                  messageType={message.type}
                >
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </MessageBubble>
              </Message>
            ))}
            
            {(isTyping || isStreaming) && (
              <TypingIndicator
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
              >
                <MessageAvatar isAgent={true}>
                  <Bot size={20} />
                </MessageAvatar>
                <div>
                  {isStreaming 
                    ? `${activeAgent.charAt(0).toUpperCase() + activeAgent.slice(1)} Agent working...`
                    : 'AI is thinking'
                  }
                  <TypingDots>
                    <span></span>
                    <span></span>
                    <span></span>
                  </TypingDots>
                </div>
              </TypingIndicator>
            )}
            
            <div ref={messagesEndRef} />
          </MessagesList>
        </MessagesContainer>

        <InputArea>
          <InputContainer>
            <InputField
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about portfolio optimization, risk management, market insights..."
              disabled={isTyping || isStreaming}
            />
            <SendButton
              onClick={handleSendMessage}
              disabled={!currentInput.trim() || isTyping || isStreaming}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Send size={20} />
            </SendButton>
          </InputContainer>
        </InputArea>
      </ChatArea>
    </ChatContainer>
  );
};

export default AgentChatPage; 