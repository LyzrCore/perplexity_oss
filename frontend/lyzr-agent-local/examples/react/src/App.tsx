import React, { useEffect, useState } from 'react';
import lyzrInstance from '../../../dist/index.esm.js';

function App() {
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeLyzr = async () => {
      try {
        await lyzrInstance.init('pk_c14a2728e715d9ea67bf');
        setIsInitialized(true);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to initialize LyzrAgent');
      }
    };

    initializeLyzr();
  }, []);

  const handleBadgePosition = (position: 'topRight' | 'topLeft' | 'reset') => {
    switch (position) {
      case 'topRight':
        lyzrInstance.setBadgePosition('20px', 'auto');
        break;
      case 'topLeft':
        lyzrInstance.setBadgePosition('auto', 'auto');
        break;
      case 'reset':
        lyzrInstance.setBadgePosition('20px', '20px');
        break;
    }
  };

  if (error) {
    return (
      <div style={{ color: 'red', padding: '20px' }}>
        Error: {error}
      </div>
    );
  }

  return (
    <div style={{
      fontFamily: 'Arial, sans-serif',
      maxWidth: '800px',
      margin: '40px auto',
      padding: '20px',
      textAlign: 'center'
    }}>
      <h1>LyzrAgent React Demo</h1>
      <p>This demo shows how to use LyzrAgent for Google authentication with Memberstack in a React application</p>
      
      <div style={{ marginTop: '20px' }}>
        <button
          onClick={() => handleBadgePosition('topRight')}
          style={{
            padding: '10px 20px',
            margin: '10px',
            background: '#4285f4',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Move Badge to Top Right
        </button>
        <button
          onClick={() => handleBadgePosition('topLeft')}
          style={{
            padding: '10px 20px',
            margin: '10px',
            background: '#4285f4',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Move Badge to Top Left
        </button>
        <button
          onClick={() => handleBadgePosition('reset')}
          style={{
            padding: '10px 20px',
            margin: '10px',
            background: '#4285f4',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Reset Badge Position
        </button>
      </div>
    </div>
  );
}

export default App;
