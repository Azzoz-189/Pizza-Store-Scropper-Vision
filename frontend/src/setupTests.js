// Import jest-dom for custom matchers
import '@testing-library/jest-dom';

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.onopen = null;
    this.onclose = null;
    this.onerror = null;
    this.onmessage = null;
    this.readyState = 1; // OPEN
    
    // Simulate connection
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 100);
  }
  
  send(data) {
    // Mock sending data
    console.log('Mock WebSocket send:', data);
  }
  
  close() {
    this.readyState = 3; // CLOSED
    if (this.onclose) this.onclose();
  }
}

// Mock window.WebSocket
global.WebSocket = MockWebSocket;

// Mock URL.createObjectURL
window.URL.createObjectURL = jest.fn();
