import React from 'react';
import styled from 'styled-components';

interface AssetAmountInputProps {
  assetClass: string;
  value: string; // USD amount as string for easy binding
  onChange: (val: string) => void;
}

const Container = styled.div`
  margin-top: 1.5rem;
`;

const Label = styled.h4`
  margin-bottom: 0.5rem;
`;

const Input = styled.input`
  width: 50%;
  min-width: 180px;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  font-size: 0.9rem;
`;

const AssetAmountInput: React.FC<AssetAmountInputProps> = ({ assetClass, value, onChange }) => {
  return (
    <Container>
      <Label>{assetClass} – total amount (USD)</Label>
      <Input
        type="number"
        placeholder="e.g. 10000"
        value={value}
        min="0"
        step="any"
        onChange={e => onChange(e.target.value)}
      />
    </Container>
  );
};

export default AssetAmountInput; 