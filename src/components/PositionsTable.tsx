import React, { useState } from 'react';
import styled from 'styled-components';

export interface PositionRow {
  id: string;
  ticker: string;
  amount: string;
  units: 'shares' | 'usd';
  valid?: boolean | null; // null/undefined = unchecked, true = ok, false = invalid
}

interface PositionsTableProps {
  assetClass: string;            // e.g. "US Equity"
  value: PositionRow[];          // current rows for this asset-class
  onChange: (rows: PositionRow[]) => void;
}

const Table = styled.div`
  width: 100%;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  overflow-x: auto;
`;

const HeaderRow = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 40px;
  background: var(--gray-50);
  padding: 0.75rem;
  font-weight: 600;
  font-size: 0.9rem;
`;

const DataRow = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 40px;
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--gray-100);
  align-items: center;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.4rem 0.5rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
`;

const Select = styled.select`
  width: 100%;
  padding: 0.4rem 0.5rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  background: var(--white);
`;

const RemoveBtn = styled.button`
  background: transparent;
  color: var(--error-red);
  border: none;
  font-size: 1.1rem;
  cursor: pointer;
`;

const AddBtn = styled.button`
  margin-top: 0.75rem;
  padding: 0.5rem 1rem;
  background: var(--gray-100);
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  cursor: pointer;
  border: none;
  &:hover {
    background: var(--gray-200);
  }
`;

const PositionsTable: React.FC<PositionsTableProps> = ({ assetClass, value, onChange }) => {
  const [rows, setRows] = useState<PositionRow[]>(value.length ? value : [emptyRow()]);

  function emptyRow(): PositionRow {
    return {
      id: crypto.randomUUID(),
      ticker: '',
      amount: '',
      units: 'shares',
      valid: null
    };
  }

  /**
   * Validate a ticker symbol by calling the backend /validate-ticker endpoint.
   */
  const validateTicker = async (ticker: string): Promise<boolean> => {
    if (!ticker) return false;
    try {
      const resp = await fetch(`/validate-ticker/${ticker.toUpperCase()}`);
      if (!resp.ok) return false;
      const data = await resp.json();
      return !!data.valid;
    } catch {
      return false;
    }
  };

  // propagate to parent whenever rows change
  const pushChange = (newRows: PositionRow[]) => {
    setRows(newRows);
    onChange(newRows);
  };

  const updateRow = (id: string, field: keyof PositionRow, newVal: string) => {
    const newRows = rows.map(r => (r.id === id ? { ...r, [field]: newVal } : r));
    pushChange(newRows);
  };

  const setRowValidity = (id: string, isValid: boolean) => {
    const newRows = rows.map(r => (r.id === id ? { ...r, valid: isValid } : r));
    pushChange(newRows);
  };

  const removeRow = (id: string) => {
    const newRows = rows.filter(r => r.id !== id);
    pushChange(newRows.length ? newRows : [emptyRow()]);
  };

  const handleTickerBlur = async (rowId: string, ticker: string) => {
    const ok = await validateTicker(ticker.trim().toUpperCase());
    setRowValidity(rowId, ok);
  };

  const addRow = () => {
    pushChange([...rows, emptyRow()]);
  };

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <h4>{assetClass} – positions</h4>
      <Table>
        <HeaderRow>
          <div>Ticker</div>
          <div>Amount</div>
          <div>Units</div>
          <div></div>
        </HeaderRow>
        {rows.map(row => (
          <DataRow key={row.id}>
            <Input
              placeholder="e.g. AAPL"
              value={row.ticker}
              style={row.valid === false ? { borderColor: 'var(--error-red)' } : undefined}
              onChange={e => updateRow(row.id, 'ticker', e.target.value.toUpperCase())}
              onBlur={e => handleTickerBlur(row.id, e.target.value)}
            />
            <Input
              type="number"
              placeholder="e.g. 100"
              value={row.amount}
              onChange={e => updateRow(row.id, 'amount', e.target.value)}
            />
            <Select
              value={row.units}
              onChange={e => updateRow(row.id, 'units', e.target.value as 'shares' | 'usd')}
            >
              <option value="shares">Shares</option>
              <option value="usd">USD</option>
            </Select>
            <RemoveBtn type="button" onClick={() => removeRow(row.id)}>&times;</RemoveBtn>
          </DataRow>
        ))}
        {/* optional inline error row */}
        {rows.map(
          row =>
            row.valid === false && (
              <div key={row.id + '-err'} style={{ gridColumn: '1 / -1', color: 'var(--error-red)', fontSize: '0.8rem', marginTop: '-0.25rem' }}>
                Unknown ticker "{row.ticker}" – please correct.
              </div>
            )
        )}
      </Table>
      <AddBtn type="button" onClick={addRow}>+ Add position</AddBtn>
    </div>
  );
};

export default PositionsTable; 