import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, Shield, Clock, CheckCircle } from 'lucide-react';
import { ClientProfile } from '../App';

interface AnalysisPageProps {
  clientProfile: ClientProfile;
  onComplete: () => void;
}

const AnalysisContainer = styled.div`
  min-height: 100vh;
  background: var(--gray-50);
  padding: 2rem;
`;

const AnalysisContent = styled.div`
  max-width: 1000px;
  margin: 0 auto;
`;

const Header = styled.div`
  text-align: center;
  margin-bottom: 3rem;
`;

const Title = styled.h1`
  margin-bottom: 1rem;
  color: var(--primary-blue);
`;

const Subtitle = styled.p`
  font-size: 1.1rem;
  color: var(--gray-600);
`;

const ProcessSteps = styled.div`
  display: grid;
  gap: 2rem;
  margin-bottom: 3rem;
`;

const ProcessStep = styled(motion.div)<{ isActive?: boolean; isCompleted?: boolean }>`
  background: var(--white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: 2rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  
  ${props => props.isActive && `
    border-left: 4px solid var(--primary-blue);
    box-shadow: var(--shadow-lg);
  `}
  
  ${props => props.isCompleted && `
    border-left: 4px solid var(--success-green);
  `}
`;

const StepIcon = styled.div<{ isActive?: boolean; isCompleted?: boolean }>`
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  ${props => props.isCompleted ? `
    background: var(--success-green);
    color: var(--white);
  ` : props.isActive ? `
    background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
    color: var(--white);
  ` : `
    background: var(--gray-200);
    color: var(--gray-500);
  `}
`;

const StepContent = styled.div`
  flex: 1;
`;

const StepTitle = styled.h3`
  margin-bottom: 0.5rem;
  color: var(--primary-blue);
`;

const StepDescription = styled.p`
  color: var(--gray-600);
  margin-bottom: 0.5rem;
`;

const StepStatus = styled.div<{ isActive?: boolean }>`
  font-size: 0.875rem;
  font-weight: 500;
  
  ${props => props.isActive ? `
    color: var(--primary-blue);
  ` : `
    color: var(--gray-500);
  `}
`;

const LoadingIndicator = styled(motion.div)`
  width: 100%;
  height: 4px;
  background: var(--gray-200);
  border-radius: var(--radius-sm);
  overflow: hidden;
  margin-top: 1rem;
`;

const LoadingBar = styled(motion.div)`
  height: 100%;
  background: linear-gradient(90deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
  border-radius: var(--radius-sm);
`;

const AnalysisPage: React.FC<AnalysisPageProps> = ({ clientProfile, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  const analysisSteps = [
    {
      icon: <BarChart3 size={24} />,
      title: "Data Integration",
      description: "Analyzing your portfolio responses and financial goals",
      duration: 2000
    },
    {
      icon: <TrendingUp size={24} />,
      title: "Market Analysis",
      description: "Fetching real-time market data and asset performance metrics",
      duration: 3000
    },
    {
      icon: <Shield size={24} />,
      title: "Risk Assessment",
      description: "Calculating risk-adjusted returns and volatility analysis",
      duration: 2500
    },
    {
      icon: <Clock size={24} />,
      title: "Optimization Engine",
      description: "Running portfolio optimization algorithms based on your constraints",
      duration: 3500
    }
  ];

  useEffect(() => {
    const runAnalysis = async () => {
      for (let i = 0; i < analysisSteps.length; i++) {
        setCurrentStep(i);
        
        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, analysisSteps[i].duration));
        
        setCompletedSteps(prev => [...prev, i]);
      }
      
      // Complete analysis
      setTimeout(() => {
        onComplete();
      }, 1000);
    };

    runAnalysis();
  }, []);

  return (
    <AnalysisContainer>
      <AnalysisContent>
        <Header>
          <Title>Portfolio Analysis in Progress</Title>
          <Subtitle>
            Our AI agents are analyzing your financial profile and market conditions 
            to create your personalized portfolio recommendations
          </Subtitle>
        </Header>

        <ProcessSteps>
          {analysisSteps.map((step, index) => (
            <ProcessStep
              key={index}
              isActive={currentStep === index}
              isCompleted={completedSteps.includes(index)}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <StepIcon 
                isActive={currentStep === index}
                isCompleted={completedSteps.includes(index)}
              >
                {completedSteps.includes(index) ? (
                  <CheckCircle size={24} />
                ) : (
                  step.icon
                )}
              </StepIcon>
              
              <StepContent>
                <StepTitle>{step.title}</StepTitle>
                <StepDescription>{step.description}</StepDescription>
                <StepStatus isActive={currentStep === index}>
                  {completedSteps.includes(index) ? (
                    "✓ Completed"
                  ) : currentStep === index ? (
                    "Processing..."
                  ) : (
                    "Pending"
                  )}
                </StepStatus>
                
                {currentStep === index && (
                  <LoadingIndicator>
                    <LoadingBar
                      initial={{ width: "0%" }}
                      animate={{ width: "100%" }}
                      transition={{ 
                        duration: step.duration / 1000,
                        ease: "linear"
                      }}
                    />
                  </LoadingIndicator>
                )}
              </StepContent>
            </ProcessStep>
          ))}
        </ProcessSteps>

        {completedSteps.length === analysisSteps.length && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            style={{
              background: 'var(--white)',
              padding: '2rem',
              borderRadius: 'var(--radius-lg)',
              boxShadow: 'var(--shadow-lg)',
              textAlign: 'center'
            }}
          >
            <CheckCircle size={48} style={{ color: 'var(--success-green)', marginBottom: '1rem' }} />
            <h3 style={{ color: 'var(--primary-blue)', marginBottom: '0.5rem' }}>
              Analysis Complete!
            </h3>
            <p style={{ color: 'var(--gray-600)' }}>
              Preparing your personalized portfolio recommendations...
            </p>
          </motion.div>
        )}
      </AnalysisContent>
    </AnalysisContainer>
  );
};

export default AnalysisPage; 