import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { TrendingUp, Shield, Zap, Users } from 'lucide-react';

interface LandingPageProps {
  onStart: () => void;
}

const LandingContainer = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
`;

const Header = styled.header`
  background: var(--white);
  box-shadow: var(--shadow-sm);
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 100;
`;

const Nav = styled.nav`
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Logo = styled.div`
  font-weight: 700;
  font-size: 1.5rem;
  color: var(--primary-blue);
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const HeroSection = styled.section`
  flex: 1;
  display: flex;
  align-items: center;
  padding: 4rem 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
`;

const HeroContent = styled.div`
  flex: 1;
  max-width: 600px;
`;

const HeroTitle = styled(motion.h1)`
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  
  @media (max-width: 768px) {
    font-size: 2.5rem;
  }
`;

const HeroSubtitle = styled(motion.p)`
  font-size: 1.25rem;
  color: var(--gray-600);
  margin-bottom: 2rem;
  line-height: 1.6;
`;

const CTAButton = styled(motion.button)`
  background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
  color: var(--white);
  padding: 1rem 2rem;
  border-radius: var(--radius-lg);
  font-size: 1.1rem;
  font-weight: 600;
  box-shadow: var(--shadow-lg);
  
  &:hover {
    box-shadow: var(--shadow-xl);
    transform: translateY(-2px);
  }
`;

const FeaturesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  margin-top: 4rem;
`;

const FeatureCard = styled(motion.div)`
  background: var(--white);
  padding: 2rem;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  text-align: center;
  
  &:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-4px);
  }
`;

const FeatureIcon = styled.div`
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-blue-light) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  color: var(--white);
`;

const FeatureTitle = styled.h3`
  margin-bottom: 0.5rem;
  color: var(--primary-blue);
`;

const FeatureDescription = styled.p`
  color: var(--gray-500);
  font-size: 0.9rem;
`;

const TrustIndicators = styled.div`
  margin-top: 3rem;
  text-align: center;
  color: var(--gray-500);
  font-size: 0.9rem;
`;

const LandingPage: React.FC<LandingPageProps> = ({ onStart }) => {
  const features = [
    {
      icon: <TrendingUp size={24} />,
      title: "Smart Portfolio Analysis",
      description: "AI-powered analysis of your current holdings with real-time market data"
    },
    {
      icon: <Shield size={24} />,
      title: "Risk-Adjusted Optimization",
      description: "Sophisticated algorithms that balance returns with your risk tolerance"
    },
    {
      icon: <Zap size={24} />,
      title: "Instant Recommendations",
      description: "Get actionable rebalancing recommendations in minutes, not hours"
    },
    {
      icon: <Users size={24} />,
      title: "Institutional-Grade Tools",
      description: "Access the same quantitative tools used by top-tier wealth managers"
    }
  ];

  return (
    <LandingContainer>
      <Header>
        <Nav>
          <Logo>
            <TrendingUp size={28} />
            Agentic Advisor
          </Logo>
        </Nav>
      </Header>

      <HeroSection>
        <HeroContent>
          <HeroTitle
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            Professional Portfolio Rebalancing, Powered by AI
          </HeroTitle>
          
          <HeroSubtitle
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            Experience institutional-grade portfolio optimization with our AI-powered advisory platform. 
            Get personalized recommendations that adapt to your goals, risk tolerance, and market conditions.
          </HeroSubtitle>

          <CTAButton
            onClick={onStart}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Start Your Portfolio Analysis
          </CTAButton>

          <FeaturesGrid>
            {features.map((feature, index) => (
              <FeatureCard
                key={index}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.6 + index * 0.1 }}
                whileHover={{ y: -4 }}
              >
                <FeatureIcon>{feature.icon}</FeatureIcon>
                <FeatureTitle>{feature.title}</FeatureTitle>
                <FeatureDescription>{feature.description}</FeatureDescription>
              </FeatureCard>
            ))}
          </FeaturesGrid>

          <TrustIndicators>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 1.2 }}
            >
              🔒 Bank-grade security • 📊 Real-time market data • 🏆 Institutional-quality analysis
            </motion.div>
          </TrustIndicators>
        </HeroContent>
      </HeroSection>
    </LandingContainer>
  );
};

export default LandingPage; 