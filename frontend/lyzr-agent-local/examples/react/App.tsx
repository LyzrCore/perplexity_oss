import React, { useEffect } from 'react';
import lyzr from 'lyzr-agent';

function App() {
  useEffect(() => {
    // Initialize LyzrAgent when component mounts
    lyzr.init('pk_c14a2728e715d9ea67bf');
  }, []);

  const handleMoveBadge = () => {
    // Move badge to top left corner
    lyzr.setBadgePosition('auto', 'auto');
  };

  const handleResetBadge = () => {
    // Reset badge to default position (bottom right)
    lyzr.setBadgePosition('20px', '20px');
  };

  return (
    <div style={{
      maxWidth: '600px',
      margin: '50px auto',
      padding: '20px',
      textAlign: 'center',
      fontFamily: 'Arial, sans-serif'
    }}>
      <h1>LyzrAgent React Example</h1>
      <p>This example demonstrates the LyzrAgent integration with React</p>

      <button
        onClick={handleMoveBadge}
        style={{
          padding: '10px 20px',
          margin: '10px',
          border: 'none',
          borderRadius: '4px',
          background: '#4285f4',
          color: 'white',
          cursor: 'pointer'
        }}
      >
        Move Badge to Top Left
      </button>

      <button
        onClick={handleResetBadge}
        style={{
          padding: '10px 20px',
          margin: '10px',
          border: 'none',
          borderRadius: '4px',
          background: '#4285f4',
          color: 'white',
          cursor: 'pointer'
        }}
      >
        Reset Badge Position
      </button>
    </div>
  );
}

export default App;
