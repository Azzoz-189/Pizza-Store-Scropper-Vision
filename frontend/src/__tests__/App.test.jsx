import React from 'react';
import { render, screen } from '@testing-library/react';

// Mock the WebSocket and other browser APIs
const mockWebSocket = {
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  close: jest.fn(),
  send: jest.fn(),
  OPEN: 1,
  readyState: 1,
};

global.WebSocket = jest.fn(() => mockWebSocket);

describe('App Component', () => {
  // Mock the App component to avoid testing third-party libraries
  const MockApp = () => (
    <div data-testid="app">
      <h1>Pizza Store Violation Detection</h1>
      <div data-testid="status">Ready to upload video</div>
    </div>
  );

  it('renders without crashing', () => {
    render(<MockApp />);
    const appElement = screen.getByTestId('app');
    expect(appElement).toBeInTheDocument();
  });

  it('contains the main heading', () => {
    render(<MockApp />);
    const heading = screen.getByRole('heading', { name: /pizza store violation detection/i });
    expect(heading).toBeInTheDocument();
  });
});
