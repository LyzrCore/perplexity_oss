# LyzrAgent Examples

This directory contains examples of how to use the LyzrAgent package in different JavaScript environments.

## Vanilla JavaScript Example

Located in the `vanilla` directory, this example shows how to use LyzrAgent in a basic HTML/JavaScript environment.

To run:
1. Build the main package first:
```bash
cd ..
npm install
npm run build
```

2. Open `vanilla/index.html` in your browser.

## React Example

Located in the `react` directory, this example demonstrates how to integrate LyzrAgent in a React application.

To run:
1. Create a new React project:
```bash
npx create-react-app my-lyzr-app --template typescript
cd my-lyzr-app
```

2. Install LyzrAgent:
```bash
npm install lyzr-agent
```

3. Replace the contents of `src/App.tsx` with the example code.

4. Start the development server:
```bash
npm start
```

## Important Notes

- Replace `'YOUR_MEMBERSTACK_PUBLIC_KEY'` with your actual Memberstack public key in both examples.
- The Google login modal will appear automatically if the user is not authenticated.
- The "Powered by Lyzr Agent Studio" badge appears in the bottom right corner by default.
- Use the buttons to test the badge position customization feature.
