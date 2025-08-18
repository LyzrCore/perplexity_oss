declare module 'lyzr-agent' {

  interface LyzrAgentInitConfig {
    pagosUrl?: string;
    agentStudioUrl?: string;
    agentStudioUrlSignup?: string;
  }
  class LyzrAgent {
    /**
   * Initializes the agent.
   * @param publicKey Optional public key to override the one provided in the constructor.
   * @param config Optional configuration object to override URLs.
   */
    init(publicKey?: string, config?: LyzrAgentInitConfig): Promise<LyzrAgent>;
    setBadgePosition(x?: string, y?: string): void;
    getKeys(): Promise<string[]>;
    getKeysUser(): Promise<any>;
    hideAppContent(): void;
    showAppContent(): void;
    logout(): void;
    onAuthStateChange(callback: (isAuthenticated: boolean) => void): () => void;
    checkCredits(): Promise<void>;
  }

  const lyzr: LyzrAgent;
  export default lyzr;
}
