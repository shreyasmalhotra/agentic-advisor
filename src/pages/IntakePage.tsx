import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, MessageCircle, Loader } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { ClientProfile } from '../App';
import axios from 'axios';

interface IntakePageProps {
  clientProfile: ClientProfile;
  onComplete: () => void;
  onUpdateProfile: (updates: Partial<ClientProfile>) => void;
  onBack?: () => void;
}

const IntakeContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--gray-50);
`;

const Header = styled.header`
  background: var(--white);
  padding: 1.5rem 0;
  box-shadow: var(--shadow-sm);
`;

const HeaderContent = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const BackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: transparent;
  color: var(--gray-600);
  padding: 0.5rem;
  border-radius: var(--radius-md);
  
  &:hover {
    background: var(--gray-100);
    color: var(--primary-blue);
  }
`;

const ProgressBar = styled.div`
  flex: 1;
  max-width: 400px;
  margin: 0 2rem;
`;

const ProgressTrack = styled.div`
  height: 8px;
  background: var(--gray-200);
  border-radius: var(--radius-sm);
  overflow: hidden;
`;

const ProgressFill = styled(motion.div)<{ progress: number }>`
  height: 100%;
  background: linear-gradient(90deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
  border-radius: var(--radius-sm);
  width: ${props => props.progress}%;
`;

const ProgressText = styled.div`
  text-align: center;
  margin-top: 0.5rem;
  color: var(--gray-600);
  font-size: 0.875rem;
`;

const ChatContainer = styled.div`
  flex: 1;
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
`;

const ChatMessages = styled.div`
  background: var(--white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: 2rem;
  margin-bottom: 2rem;
  min-height: 400px;
  max-height: 600px;
  overflow-y: auto;
`;

const Message = styled(motion.div)<{ isAgent?: boolean }>`
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  align-items: flex-start;
  
  ${props => props.isAgent && `
    flex-direction: row;
  `}
  
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
  
  ${props => props.isAgent ? `
    background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
    color: var(--white);
  ` : `
    background: var(--gray-200);
    color: var(--gray-600);
  `}
`;

const MessageBubble = styled.div<{ isAgent?: boolean }>`
  max-width: 70%;
  padding: 1rem 1.25rem;
  border-radius: var(--radius-lg);
  
  ${props => props.isAgent ? `
    background: var(--gray-100);
    color: var(--gray-800);
    border-bottom-left-radius: var(--radius-sm);
  ` : `
    background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
    color: var(--white);
    border-bottom-right-radius: var(--radius-sm);
  `}
  
  /* Markdown styling */
  h1, h2, h3, h4, h5, h6 {
    margin: 0.5rem 0;
  }
  
  p {
    margin: 0.5rem 0;
    line-height: 1.5;
  }
  
  strong {
    font-weight: 600;
  }
  
  hr {
    margin: 1rem 0;
    border: none;
    border-top: 1px solid ${props => props.isAgent ? 'var(--gray-300)' : 'rgba(255,255,255,0.3)'};
  }
`;

const InputContainer = styled.div`
  background: var(--white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: 1.5rem;
`;

const InputField = styled.textarea`
  width: 100%;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-md);
  padding: 1rem;
  font-size: 1rem;
  resize: vertical;
  min-height: 80px;
  
  &:focus {
    border-color: var(--primary-blue);
    box-shadow: 0 0 0 3px rgba(26, 54, 93, 0.1);
  }
`;

const SendButton = styled(motion.button)<{ disabled?: boolean }>`
  background: ${props => props.disabled ? 'var(--gray-300)' : 'linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%)'};
  color: var(--white);
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  font-weight: 600;
  margin-top: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  
  &:hover {
    ${props => !props.disabled && `
      transform: translateY(-1px);
      box-shadow: var(--shadow-lg);
    `}
  }
`;

const LoadingDots = styled.div`
  display: flex;
  gap: 4px;
  
  span {
    width: 6px;
    height: 6px;
    background: var(--gray-400);
    border-radius: 50%;
    animation: loading 1.4s infinite ease-in-out;
    
    &:nth-child(1) { animation-delay: -0.32s; }
    &:nth-child(2) { animation-delay: -0.16s; }
  }
  
  @keyframes loading {
    0%, 80%, 100% { opacity: 0.3; }
    40% { opacity: 1; }
  }
`;

const IntakePage: React.FC<IntakePageProps> = ({ clientProfile, onComplete, onUpdateProfile, onBack }) => {
  const [messages, setMessages] = useState<Array<{id: string, content: string, isAgent: boolean}>>([]);
  const [currentInput, setCurrentInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [questionsCompleted, setQuestionsCompleted] = useState(0);
  const hasInitializedRef = useRef(false);

  useEffect(() => {
    // Start the conversation only once, even in React StrictMode
    if (!hasInitializedRef.current) {
      hasInitializedRef.current = true;
      handleAgentInteraction(null);
    }
  }, []);

  const handleAgentInteraction = async (userInput: string | null) => {
    setIsLoading(true);
    
    try {
      const response = await axios.post('/agent/intake', {
        session_id: clientProfile.sessionId,
        user_input: userInput
      });

      // Add agent message
      const agentMessage = {
        id: Date.now().toString(),
        content: response.data.response,
        isAgent: true
      };
      
      setMessages(prev => {
        // If this is the first call and we already have messages, don't duplicate
        if (userInput === null && prev.length > 0) {
          return prev;
        }
        return [...prev, agentMessage];
      });
      
      // Update progress based on responses
      const responseCount = Object.keys(clientProfile.responses).length;
      setQuestionsCompleted(responseCount);
      
      const progress = Math.min((responseCount / 10) * 100, 100);
      onUpdateProfile({ progress });
      
      // Check if completed
      if (responseCount >= 10) {
        setTimeout(() => onComplete(), 2000);
      }
      
    } catch (error) {
      console.error('Error communicating with agent:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: "I apologize, but I'm having trouble connecting right now. Please try again.",
        isAgent: true
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!currentInput.trim() || isLoading) return;

    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      content: currentInput,
      isAgent: false
    };
    
    setMessages(prev => [...prev, userMessage]);
    const inputToSend = currentInput;
    setCurrentInput('');
    
    // Send to agent
    await handleAgentInteraction(inputToSend);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <IntakeContainer>
      <Header>
        <HeaderContent>
          <BackButton onClick={() => onBack && onBack()}>
            <ChevronLeft size={20} />
            Back
          </BackButton>
          
          <ProgressBar>
            <ProgressTrack>
              <ProgressFill
                progress={clientProfile.progress}
                initial={{ width: 0 }}
                animate={{ width: `${clientProfile.progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </ProgressTrack>
            <ProgressText>
              Question {questionsCompleted} of 10 • {Math.round(clientProfile.progress)}% Complete
            </ProgressText>
          </ProgressBar>
          
          <div style={{ width: '60px' }} /> {/* Spacer for balance */}
        </HeaderContent>
      </Header>

      <ChatContainer>
        <ChatMessages>
          {messages.map((message) => (
            <Message
              key={message.id}
              isAgent={message.isAgent}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <MessageAvatar isAgent={message.isAgent}>
                {message.isAgent ? <MessageCircle size={20} /> : 'Y'}
              </MessageAvatar>
              <MessageBubble isAgent={message.isAgent}>
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </MessageBubble>
            </Message>
          ))}
          
          {isLoading && (
            <Message isAgent={true}>
              <MessageAvatar isAgent={true}>
                <MessageCircle size={20} />
              </MessageAvatar>
              <MessageBubble isAgent={true}>
                <LoadingDots>
                  <span></span>
                  <span></span>
                  <span></span>
                </LoadingDots>
              </MessageBubble>
            </Message>
          )}
        </ChatMessages>

        <InputContainer>
          <InputField
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your response here..."
            disabled={isLoading}
          />
          <SendButton
            onClick={handleSendMessage}
            disabled={!currentInput.trim() || isLoading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isLoading ? <Loader size={16} className="animate-spin" /> : <ChevronRight size={16} />}
            Send Response
          </SendButton>
        </InputContainer>
      </ChatContainer>
    </IntakeContainer>
  );
};

export default IntakePage; 