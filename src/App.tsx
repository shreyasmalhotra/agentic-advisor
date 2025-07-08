import React, { useState } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import LandingPage from './pages/LandingPage';
import QuestionnaireForm from './pages/QuestionnaireForm';
import AnalysisPage from './pages/AnalysisPage';
import AgentChatPage from './pages/AgentChatPage';
import { GlobalStyles } from './styles/GlobalStyles';

export type WorkflowStep = 'landing' | 'questionnaire' | 'analysis' | 'chat' | 'complete';

export interface ClientProfile {
  sessionId: string;
  responses: Record<string, string>;
  currentStep: WorkflowStep;
  progress: number;
}

const AppContainer = styled.div`
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
`;

const App: React.FC = () => {
  const [clientProfile, setClientProfile] = useState<ClientProfile>({
    sessionId: `session_${Date.now()}`,
    responses: {},
    currentStep: 'landing',
    progress: 0
  });

  const updateClientProfile = (updates: Partial<ClientProfile>) => {
    setClientProfile(prev => ({ ...prev, ...updates }));
  };

  const initializeSession = async () => {
    try {
      const response = await fetch('/init-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: clientProfile.sessionId })
      });
      
      const result = await response.json();
      if (!result.success) {
        console.error('Failed to initialize session:', result.message);
      }
    } catch (error) {
      console.error('Error initializing session:', error);
    }
  };

  const renderCurrentStep = () => {
    switch (clientProfile.currentStep) {
      case 'landing':
        return (
          <LandingPage 
            onStart={async () => {
              await initializeSession();
              updateClientProfile({ currentStep: 'questionnaire', progress: 10 });
            }}
          />
        );
      case 'questionnaire':
        return (
          <QuestionnaireForm 
            clientProfile={clientProfile}
            onComplete={(responses) => updateClientProfile({ 
              responses, 
              currentStep: 'analysis', 
              progress: 50 
            })}
            onBack={() => updateClientProfile({ currentStep: 'landing', progress: 0 })}
          />
        );
      case 'analysis':
        return (
          <AnalysisPage 
            clientProfile={clientProfile}
            onComplete={() => updateClientProfile({ currentStep: 'chat', progress: 100 })}
          />
        );
      case 'chat':
        return (
          <AgentChatPage 
            clientProfile={clientProfile}
            responses={clientProfile.responses}
            onComplete={() => updateClientProfile({ currentStep: 'complete', progress: 100 })}
          />
        );
      default:
        return <div>Loading...</div>;
    }
  };

  return (
    <AppContainer>
      <GlobalStyles />
      <AnimatePresence mode="wait">
        <motion.div
          key={clientProfile.currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
        >
          {renderCurrentStep()}
        </motion.div>
      </AnimatePresence>
    </AppContainer>
  );
};

export default App; 