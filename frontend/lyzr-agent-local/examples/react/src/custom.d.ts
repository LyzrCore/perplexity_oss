declare module '../../../dist/index.esm.js' {
  interface LyzrAgent {
    init(publicKey: string): Promise<LyzrAgent>;
    setBadgePosition(x?: string, y?: string): void;
  }

  const lyzrInstance: LyzrAgent;
  export default lyzrInstance;
}
