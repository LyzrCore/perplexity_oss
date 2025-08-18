# LyzrAgent

A lightweight authentication package that integrates Memberstack's Google login functionality with a floating badge.

## Installation

```bash
npm install lyzr-agent
# or
yarn add lyzr-agent
```

## Usage

### Basic Setup

```javascript
import lyzr from 'lyzr-agent';

// Initialize with your Memberstack public key
lyzr.init('your_memberstack_public_key');
```

### Customizing Badge Position

```javascript
// Change badge position (distances from edges in pixels)
lyzr.setBadgePosition('30px', '40px');
```

### Features

- Easy integration with Memberstack authentication
- Google login modal
- Customizable floating badge
- Works with any JavaScript-based project (React, Vue, vanilla JS, etc.)
- TypeScript support

### Requirements

- Memberstack account and public key
- Modern browser environment

## License

MIT
