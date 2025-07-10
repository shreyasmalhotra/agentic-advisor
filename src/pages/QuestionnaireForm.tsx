import React, { useState } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { ChevronLeft, ChevronRight, CheckCircle, Loader } from 'lucide-react';
import { ClientProfile } from '../App';
import axios from 'axios';
import PositionsTable, { PositionRow } from '../components/PositionsTable';
import AssetAmountInput from '../components/AssetAmountInput';

interface QuestionnaireFormProps {
  clientProfile: ClientProfile;
  onComplete: (responses: Record<string, string>) => void;
  onBack?: () => void;
}

const FormContainer = styled.div`
  min-height: 100vh;
  background: var(--gray-50);
  padding: 2rem;
`;

const FormContent = styled.div`
  max-width: 800px;
  margin: 0 auto;
`;

const Header = styled.div`
  background: var(--white);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  padding: 2rem;
  border-bottom: 3px solid var(--primary-blue);
  margin-bottom: 0;
`;

const Title = styled.h1`
  color: var(--primary-blue);
  margin-bottom: 0.5rem;
`;

const Subtitle = styled.p`
  color: var(--gray-600);
  font-size: 1.1rem;
`;

const FormSection = styled(motion.div)`
  background: var(--white);
  margin-bottom: 0;
  box-shadow: var(--shadow-sm);
  
  &:last-child {
    border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  }
`;

const Question = styled.div`
  padding: 2rem;
  border-bottom: 1px solid var(--gray-200);
  
  &:last-child {
    border-bottom: none;
  }
`;

const QuestionLabel = styled.label`
  display: block;
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--primary-blue);
  margin-bottom: 0.5rem;
`;

const QuestionNumber = styled.span`
  color: var(--gray-500);
  font-weight: 400;
  margin-right: 0.5rem;
`;

const RequiredIndicator = styled.span`
  color: var(--error-red);
  margin-left: 0.25rem;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-md);
  font-size: 1rem;
  transition: border-color 0.2s;
  
  &:focus {
    border-color: var(--primary-blue);
    box-shadow: 0 0 0 3px rgba(26, 54, 93, 0.1);
  }
`;

const TextArea = styled.textarea`
  width: 100%;
  padding: 0.75rem;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-md);
  font-size: 1rem;
  min-height: 100px;
  resize: vertical;
  transition: border-color 0.2s;
  
  &:focus {
    border-color: var(--primary-blue);
    box-shadow: 0 0 0 3px rgba(26, 54, 93, 0.1);
  }
`;

const Select = styled.select`
  width: 100%;
  padding: 0.75rem;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius-md);
  font-size: 1rem;
  background: var(--white);
  transition: border-color 0.2s;
  
  &:focus {
    border-color: var(--primary-blue);
    box-shadow: 0 0 0 3px rgba(26, 54, 93, 0.1);
  }
`;

const RadioGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
`;

const RadioOption = styled.label`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background: var(--gray-50);
  }
`;

const RadioInput = styled.input`
  margin: 0;
`;

const OtherInputContainer = styled(motion.div)`
  margin-top: 0.5rem;
  margin-left: 2rem;
`;

const OtherInput = styled.input`
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 2px solid var(--gray-300);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  transition: border-color 0.2s;
  
  &:focus {
    border-color: var(--primary-blue);
    box-shadow: 0 0 0 3px rgba(26, 54, 93, 0.1);
  }
`;

const SubmitSection = styled.div`
  background: var(--white);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  padding: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: var(--shadow-md);
`;

const BackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: transparent;
  color: var(--gray-600);
  padding: 0.75rem 1rem;
  border-radius: var(--radius-md);
  
  &:hover {
    background: var(--gray-100);
    color: var(--primary-blue);
  }
`;

const SubmitButton = styled(motion.button)<{ disabled?: boolean }>`
  background: ${props => props.disabled ? 'var(--gray-300)' : 'linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%)'};
  color: var(--white);
  padding: 0.75rem 2rem;
  border-radius: var(--radius-md);
  font-weight: 600;
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

const ProgressInfo = styled.div`
  color: var(--gray-600);
  font-size: 0.9rem;
`;

const CheckboxGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
`;

const CheckboxOption = styled.label`
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background: var(--gray-50);
  }
`;

const CheckboxInput = styled.input`
  margin: 0;
  cursor: pointer;
`;

const ErrorMessage = styled.div`
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-md);
  padding: 1rem;
  margin-top: 1rem;
  color: #dc2626;
  font-size: 0.9rem;
  line-height: 1.5;
`;

const QuestionnaireForm: React.FC<QuestionnaireFormProps> = ({ clientProfile, onComplete, onBack }) => {
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [checkboxResponses, setCheckboxResponses] = useState<Record<string, string[]>>({});
  const [otherInputs, setOtherInputs] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationError, setValidationError] = useState<string>('');
  const [positions, setPositions] = useState<Record<string, PositionRow[]>>({});
  const [assetAmounts, setAssetAmounts] = useState<Record<string, string>>({});

  // Categories that only need a dollar amount instead of detailed tickers
  const simpleAssetClasses = [
    'Emerging Markets',
    'Bond Portfolio (Government & Corporate)',
    'Balanced Portfolio (Stocks & Bonds)',
    'Real Estate (REITs)',
    'Mixed Portfolio (Multiple Asset Classes)',
    'Other' // treat custom "Other" holdings as a simple dollar amount input
  ];

  // Helper to update position rows for a given asset-class
  const updatePositions = (assetClass: string, rows: PositionRow[]) => {
    setPositions(prev => ({ ...prev, [assetClass]: rows }));
  };

  const updateAssetAmount = (assetClass: string, amountStr: string) => {
    setAssetAmounts(prev => ({ ...prev, [assetClass]: amountStr }));
  };

  const questions = [
    {
      id: 'investment_goal',
      label: 'What\'s your primary investment goal?',
      type: 'radio',
      options: ['Growth', 'Income', 'Preservation', 'Balanced Growth & Income']
    },
    {
      id: 'time_horizon',
      label: 'What\'s your target time horizon?',
      type: 'radio',
      options: ['Less than 3 years', '3-5 years', '5-10 years', '10+ years']
    },
    {
      id: 'risk_tolerance',
      label: 'How would you rate your risk tolerance?',
      type: 'radio',
      options: ['1 - Very Conservative', '2 - Conservative', '3 - Moderate', '4 - Aggressive', '5 - Very Aggressive']
    },
    {
      id: 'portfolio_size',
      label: 'What is the approximate size of your current portfolio (in USD)?',
      type: 'select',
      options: ['Under $10,000', '$10,000 - $50,000', '$50,000 - $100,000', '$100,000 - $500,000', '$500,000 - $1M', 'Over $1M']
    },
    {
      id: 'current_assets',
      label: 'Which major asset classes do you currently hold? (Select all that apply)',
      type: 'checkbox',
      options: [
        'US Equity (S&P 500, Large Cap stocks)',
        'Technology Focused (Nasdaq, Tech stocks)',
        'Diversified US Market (Total Stock Market)',
        'International Equity (Developed Markets)',
        'Emerging Markets',
        'Bond Portfolio (Government & Corporate)',
        'Balanced Portfolio (Stocks & Bonds)',
        'Real Estate (REITs)',
        'Mixed Portfolio (Multiple Asset Classes)'
      ]
    },
    {
      id: 'constraints',
      label: 'Do you have any sector or geographic constraints/preferences?',
      type: 'textarea',
      placeholder: 'e.g., ESG focus, avoid certain sectors, geographic preferences...'
    },
    {
      id: 'liquidity_needs',
      label: 'How much cash or liquidity buffer do you want to keep available?',
      type: 'radio',
      options: ['3-6 months expenses', '6-12 months expenses', '1-2 years expenses', 'Minimal cash (growth focus)']
    },
    {
      id: 'esg_preferences',
      label: 'Do you have any ethical or sustainable investing preferences?',
      type: 'radio',
      options: ['No specific preferences', 'ESG-focused investments', 'Avoid specific sectors', 'Impact investing focus']
    },
    {
      id: 'fee_sensitivity',
      label: 'How sensitive are you to fees?',
      type: 'radio',
      options: ['Low - Focus on performance', 'Medium - Balance of cost and performance', 'High - Minimize all costs']
    },
    {
      id: 'rebalance_frequency',
      label: 'How often would you like to rebalance your portfolio?',
      type: 'radio',
      options: ['Monthly', 'Quarterly', 'Semi-annually', 'Annually', 'As needed based on drift']
    }
  ];

  const handleInputChange = (questionId: string, value: string) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: value
    }));
    
    // Clear the other input if not selecting "Other"
    if (value !== 'Other' && otherInputs[questionId]) {
      setOtherInputs(prev => ({
        ...prev,
        [questionId]: ''
      }));
    }
    
    // Clear validation error when user changes input
    setValidationError('');
  };

  const handleCheckboxChange = (questionId: string, value: string, checked: boolean) => {
    setCheckboxResponses(prev => {
      const current = prev[questionId] || [];
      if (checked) {
        return {
          ...prev,
          [questionId]: [...current, value]
        };
      } else {
        return {
          ...prev,
          [questionId]: current.filter(item => item !== value)
        };
      }
    });
    
    // Clear validation error when user changes selection
    setValidationError('');

    // Bootstrap position or amount state for newly selected asset-class
    if (checked) {
      if (simpleAssetClasses.includes(value)) {
        if (!assetAmounts[value]) {
          setAssetAmounts(prev => ({ ...prev, [value]: '' }));
        }
      } else {
        if (!positions[value]) {
          setPositions(prev => ({ ...prev, [value]: [] }));
        }
      }
    } else {
      // remove deselected asset class
      setPositions(prev => {
        const { [value]: _, ...rest } = prev;
        return rest;
      });
      setAssetAmounts(prev => {
        const { [value]: _, ...rest } = prev;
        return rest;
      });
    }
  };

  const handleOtherInputChange = (questionId: string, value: string) => {
    setOtherInputs(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const getEffectiveResponse = (questionId: string) => {
    const question = questions.find(q => q.id === questionId);
    
    if (question?.type === 'checkbox') {
      const selections = checkboxResponses[questionId] || [];
      const otherIndex = selections.findIndex(s => s === 'Other');
      
      if (otherIndex >= 0 && otherInputs[questionId]) {
        const modifiedSelections = [...selections];
        modifiedSelections[otherIndex] = `Other: ${otherInputs[questionId]}`;
        return modifiedSelections.join(', ');
      }
      
      return selections.join(', ');
    }
    
    const response = responses[questionId];
    if (response === 'Other' && otherInputs[questionId]) {
      return `Other: ${otherInputs[questionId]}`;
    }
    return response;
  };

  const validateHoldings = (holdings: string): boolean => {
    if (!holdings || holdings.trim() === '') return false;
    
    // Check if holdings can be mapped to valid tickers
    const holdingsLower = holdings.toLowerCase();
    
    // Known mappable patterns
    const validPatterns = [
      'us equity', 's&p 500', 'large cap',
      'technology focused', 'nasdaq', 'tech stocks',
      'diversified us market', 'total stock market',
      'international equity', 'developed markets',
      'emerging markets',
      'bond portfolio', 'government', 'corporate',
      'balanced portfolio', 'stocks', 'bonds',
      'real estate', 'reits',
      'mixed portfolio', 'multiple asset classes'
    ];
    
    // Check if any valid pattern is found
    const hasValidPattern = validPatterns.some(pattern => 
      holdingsLower.includes(pattern.toLowerCase())
    );
    
    // If it contains "Other:" check if it's something we can potentially map
    if (holdingsLower.includes('other:')) {
      const otherText = holdingsLower.split('other:')[1]?.trim();
      if (otherText) {
        // Check if the "Other" text contains recognizable investment terms
        const recognizableTerms = [
          'stock', 'stocks', 'equity', 'equities', 'shares',
          'bond', 'bonds', 'treasury', 'corporate',
          'etf', 'fund', 'mutual fund', 'index',
          'sp 500', 's&p', 'nasdaq', 'russell',
          'international', 'global', 'emerging', 'developed',
          'real estate', 'reit', 'commodity', 'gold', 'silver',
          'cash', 'money market', 'savings'
        ];
        
        return recognizableTerms.some(term => otherText.includes(term));
      }
      return false;
    }
    
    return hasValidPattern;
  };

  const isFormComplete = () => {
    return questions.every(q => {
      if (q.type === 'checkbox') {
        const selections = checkboxResponses[q.id] || [];
        if (selections.length === 0) return false;
        
        // If "Other" is selected, make sure the custom input is filled
        if (selections.includes('Other')) {
          return otherInputs[q.id]?.trim();
        }
        
        // For each selected asset class ensure detailed positions or amount provided
        for (const ac of selections) {
          if (simpleAssetClasses.includes(ac)) {
            const amt = assetAmounts[ac];
            if (!amt || parseFloat(amt) <= 0) return false;
          } else {
            const rows = positions[ac] || [];
            if (rows.length === 0 || rows.some(r => !r.ticker || !r.amount)) return false;
          }
        }
        return true;
      }
      
      const response = responses[q.id];
      if (!response?.trim()) return false;
      
      // If "Other" is selected, make sure the custom input is filled
      if (response === 'Other' && q.type === 'radio') {
        return otherInputs[q.id]?.trim();
      }
      
      return true;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isFormComplete() || isSubmitting) return;

    setIsSubmitting(true);
    setValidationError('');
    
    try {
      // Extra validation – ensure all position rows have valid tickers and amounts
      let positionsInvalid = false;
      Object.values(positions).forEach(arr => {
        arr.forEach(r => {
          if (!r.ticker || !r.amount || r.valid === false || r.valid == null) {
            positionsInvalid = true;
          }
        });
      });
      // validate simple amounts
      Object.entries(assetAmounts).forEach(([ac, amt]) => {
        if (simpleAssetClasses.includes(ac) && (!amt || parseFloat(amt) <= 0)) {
          positionsInvalid = true;
        }
      });
      if (positionsInvalid) {
        setValidationError('One or more positions have invalid or missing tickers/amounts. Please correct them before submitting.');
        setIsSubmitting(false);
        return;
      }
      // Format portfolio data
      const processedResponses = { ...responses };
      
      // Ensure we have the critical fields
      processedResponses.investment_goal = processedResponses.investment_goal || 'Growth';
      processedResponses.risk_tolerance = processedResponses.risk_tolerance || '3 - Moderate';
      processedResponses.time_horizon = processedResponses.time_horizon || '5+ years';
      
      // Format positions data
      const combined: Record<string, Array<{
        id: string;
        ticker: string;
        amount: string;
        units: 'shares' | 'usd';
        valid: boolean;
      }>> = {};
      
      // Add structured positions
      Object.entries(positions).forEach(([assetClass, rows]) => {
        if (rows.length > 0) {
          combined[assetClass] = rows.map(row => ({
            ...row,
            id: crypto.randomUUID(),
            valid: true
          }));
        }
      });
      
      // Add simple asset amounts as USD positions
      Object.entries(assetAmounts).forEach(([ac, amtStr]) => {
        if (!simpleAssetClasses.includes(ac)) return;
        const amt = parseFloat(amtStr);
        if (!amt || isNaN(amt)) return;
        combined[ac] = [
          {
            id: crypto.randomUUID(),
            ticker: ac.toUpperCase(),
            amount: amtStr,
            units: 'usd',
            valid: true,
          },
        ];
      });
      
      // Always include positions data, even if empty
      processedResponses.positions = JSON.stringify(combined);
      
      // Save to Supabase
      await axios.post('/submit-questionnaire', {
        session_id: clientProfile.sessionId,
        responses: processedResponses
      });
      
      // Success - proceed to next step
      onComplete(processedResponses);
    } catch (error) {
      console.error('Error submitting questionnaire:', error);
      setValidationError('Failed to submit questionnaire. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderQuestion = (question: any, index: number) => {
    const value = responses[question.id] || '';
    const checkboxValues = checkboxResponses[question.id] || [];

    return (
      <Question key={question.id}>
        <QuestionLabel>
          <QuestionNumber>{index + 1}.</QuestionNumber>
          {question.label}
          <RequiredIndicator>*</RequiredIndicator>
        </QuestionLabel>
        
        {question.type === 'checkbox' && (
          <CheckboxGroup>
            {question.options.map((option: string) => (
              <CheckboxOption key={option}>
                <CheckboxInput
                  type="checkbox"
                  value={option}
                  checked={checkboxValues.includes(option)}
                  onChange={(e) => handleCheckboxChange(question.id, option, e.target.checked)}
                />
                {option}
              </CheckboxOption>
            ))}
            <CheckboxOption>
              <CheckboxInput
                type="checkbox"
                value="Other"
                checked={checkboxValues.includes('Other')}
                onChange={(e) => handleCheckboxChange(question.id, 'Other', e.target.checked)}
              />
              Other (please specify)
            </CheckboxOption>
            {checkboxValues.includes('Other') && (
              <OtherInputContainer
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
              >
                <OtherInput
                  type="text"
                  placeholder="Please specify your holdings..."
                  value={otherInputs[question.id] || ''}
                  onChange={(e) => handleOtherInputChange(question.id, e.target.value)}
                  autoFocus
                />
              </OtherInputContainer>
            )}
            {question.id === 'current_assets' && checkboxValues.map((ac: string) => (
              simpleAssetClasses.includes(ac) ? (
                <AssetAmountInput
                  key={ac}
                  assetClass={ac}
                  value={assetAmounts[ac] || ''}
                  onChange={(val) => updateAssetAmount(ac, val)}
                />
              ) : (
                <PositionsTable
                  key={ac}
                  assetClass={ac}
                  value={positions[ac] || []}
                  onChange={(rows) => updatePositions(ac, rows)}
                />
              )
            ))}
          </CheckboxGroup>
        )}
        
        {question.type === 'radio' && (
          <RadioGroup>
            {question.options.map((option: string) => (
              <RadioOption key={option}>
                <RadioInput
                  type="radio"
                  name={question.id}
                  value={option}
                  checked={value === option}
                  onChange={(e) => handleInputChange(question.id, e.target.value)}
                />
                {option}
              </RadioOption>
            ))}
            <RadioOption>
              <RadioInput
                type="radio"
                name={question.id}
                value="Other"
                checked={value === 'Other'}
                onChange={(e) => handleInputChange(question.id, e.target.value)}
              />
              Other (please specify)
            </RadioOption>
            {value === 'Other' && (
              <OtherInputContainer
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.2 }}
              >
                <OtherInput
                  type="text"
                  placeholder="Please specify your answer..."
                  value={otherInputs[question.id] || ''}
                  onChange={(e) => handleOtherInputChange(question.id, e.target.value)}
                  autoFocus
                />
              </OtherInputContainer>
            )}
          </RadioGroup>
        )}
        
        {question.type === 'select' && (
          <Select
            value={value}
            onChange={(e) => handleInputChange(question.id, e.target.value)}
            required
          >
            <option value="">Select an option...</option>
            {question.options.map((option: string) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </Select>
        )}
        
        {question.type === 'textarea' && (
          <TextArea
            value={value}
            onChange={(e) => handleInputChange(question.id, e.target.value)}
            placeholder={question.placeholder}
            required
          />
        )}
        
        {question.type === 'input' && (
          <Input
            type="text"
            value={value}
            onChange={(e) => handleInputChange(question.id, e.target.value)}
            placeholder={question.placeholder}
            required
          />
        )}
      </Question>
    );
  };

  return (
    <FormContainer>
      <FormContent>
        <Header>
          <Title>Portfolio Analysis Questionnaire</Title>
          <Subtitle>
            Please answer all questions to help us understand your investment goals and preferences. 
            This will enable our AI agents to provide personalized portfolio recommendations.
          </Subtitle>
        </Header>

        <form onSubmit={handleSubmit}>
          <FormSection
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            {questions.map((question, index) => renderQuestion(question, index))}
          </FormSection>

          {validationError && (
            <ErrorMessage>
              <strong>Validation Error:</strong> {validationError}
            </ErrorMessage>
          )}

          <SubmitSection>
            <BackButton type="button" onClick={() => onBack && onBack()}>
              <ChevronLeft size={20} />
              Back
            </BackButton>
            
            <ProgressInfo>
              {questions.filter(q => {
                if (q.type === 'checkbox') {
                  const selections = checkboxResponses[q.id] || [];
                  if (selections.length === 0) return false;
                  if (selections.includes('Other')) {
                    return otherInputs[q.id]?.trim();
                  }
                  // For each selected asset class ensure detailed positions or amount provided
                  for (const ac of selections) {
                    if (simpleAssetClasses.includes(ac)) {
                      const amt = assetAmounts[ac];
                      if (!amt || parseFloat(amt) <= 0) return false;
                    } else {
                      const rows = positions[ac] || [];
                      if (rows.length === 0 || rows.some(r => !r.ticker || !r.amount)) return false;
                    }
                  }
                  return true;
                }
                
                const response = responses[q.id];
                if (!response?.trim()) return false;
                if (response === 'Other' && q.type === 'radio') {
                  return otherInputs[q.id]?.trim();
                }
                return true;
              }).length} of {questions.length} questions completed
            </ProgressInfo>
            
            <SubmitButton
              type="submit"
              disabled={!isFormComplete() || isSubmitting}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {isSubmitting ? (
                <Loader size={16} className="animate-spin" />
              ) : isFormComplete() ? (
                <CheckCircle size={16} />
              ) : (
                <ChevronRight size={16} />
              )}
              {isSubmitting ? 'Submitting...' : 'Start Analysis'}
            </SubmitButton>
          </SubmitSection>
        </form>
      </FormContent>
    </FormContainer>
  );
};

export default QuestionnaireForm; 