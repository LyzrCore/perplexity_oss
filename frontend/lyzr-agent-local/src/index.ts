"use client";

import memberstackDom from "@memberstack/dom";

class LyzrAgent {
  private memberstack: any;
  private badge: HTMLElement | null = null;
  private modal: HTMLElement | null = null;
  private isAuthenticated = false;
  private isLoading = false;
  public token: string | null = null;
  private publicKey: string = "";
  private apiKey: string = "";
  private authStateCallbacks: ((isAuthenticated: boolean) => void)[] = [];
  //private pagosUrl = "https://pagos-prod.studio.lyzr.ai";
  // private pagosUrl = "https://pagos-dev.test.studio.lyzr.ai";
  // private agentStudioUrl = "https://dev.test.studio.lyzr.ai/auth/sign-in";
  // private agentStudioUrlSignup = "https://dev.test.studio.lyzr.ai/auth/sign-up";
  private pagosUrl = "https://pagos-prod.studio.lyzr.ai";
  private agentStudioUrl = "https://studio.lyzr.ai/auth/sign-in";
  private agentStudioUrlSignup = "https://studio.lyzr.ai/auth/sign-up";
  private badgePosition = {
    x: "right: 20px",
    y: "bottom: 20px",
  };
  private creditWarningModal: HTMLElement | null = null;
  private creditErrorModal: HTMLElement | null = null;

  constructor(publicKey: string) {
    console.log("Initializing LyzrAgent");
    if (!publicKey) {
      throw new Error("Public key is required");
    }

    this.publicKey = publicKey;
    // Initialize Memberstack correctly
    this.memberstack = memberstackDom.init({
      publicKey,
      sessionDurationDays: 30,
    });
  }

  public async init(
    publicKey?: string,
    config?: {
      pagosUrl?: string;
      agentStudioUrl?: string;
      agentStudioUrlSignup?: string;
    }
  ): Promise<LyzrAgent> {
    try {
      // Update public key if provided; else ensure one exists
      if (publicKey) {
        this.publicKey = publicKey;
        // Reinitialize Memberstack with the new public key
        this.memberstack = memberstackDom.init({
          publicKey: this.publicKey,
          sessionDurationDays: 30,
        });
      } else if (!this.publicKey) {
        throw new Error("Public key is required");
      }

      // Update URLs from config if provided, otherwise use defaults
      if (config) {
        this.pagosUrl = config.pagosUrl || this.pagosUrl;
        this.agentStudioUrl = config.agentStudioUrl || this.agentStudioUrl;
        this.agentStudioUrlSignup =
          config.agentStudioUrlSignup || this.agentStudioUrlSignup;
      }

      console.log("Starting initialization");
      // Create elements first
      this.createLoginModal();
      this.createBadge();

      // Hide the app content initially
      console.log("Hiding app content");
      this.hideAppContent();

      // Check for token in URL for previous authentication
      console.log("Checking URL for token query param");
      await this.checkBearerAuth();

      // Check auth status and show/hide content accordingly
      console.log("Checking auth status");
      await this.checkAuthStatus();

      // Set up auth state listener
      this.setupAuthStateListener();

      console.log("Initialization complete");
      return this;
    } catch (error) {
      console.error("Error during initialization:", error);
      throw error;
    }
  }

  private async checkBearerAuth() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("token");

    if (token) {
      this.token = token;
      const res = await fetch("https://client.memberstack.com/member", {
        method: "GET",
        headers: {
          accept: "application/json",
          "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
          Authorization: `Bearer ${token}`,
          "x-api-key": this.publicKey,
        },
      });
      const response: any = await res.json();
      localStorage.setItem("_ms-mem", JSON.stringify(response?.data ?? "{}"));
      localStorage.setItem("_ms-mid", token);
      const date = new Date();
      let expires = "";
      date.setTime(date.getTime() + 15 * 24 * 60 * 60 * 1000);
      expires = "; expires=" + date.toUTCString();
      document.cookie = "_ms-mid=" + token + expires;
      document.cookie = "user_id=" + response?.data?.id;
      this.notifyAuthStateChange();

      return null;
    }
  }

  private setupAuthStateListener() {
    // Check auth state periodically
    setInterval(async () => {
      const member = await this.memberstack.getMemberCookie();
      const newAuthState = !!member;
      if (newAuthState !== this.isAuthenticated) {
        this.isAuthenticated = newAuthState;
        this.token = member;
        this.notifyAuthStateChange();
      }
    }, 1000); // Check every second
  }

  private notifyAuthStateChange() {
    this.authStateCallbacks.forEach((callback) => {
      callback(this.isAuthenticated);
    });
  }

  public onAuthStateChange(callback: (isAuthenticated: boolean) => void) {
    this.authStateCallbacks.push(callback);
    // Immediately call with current state
    callback(this.isAuthenticated);
    // Return unsubscribe function
    return () => {
      this.authStateCallbacks = this.authStateCallbacks.filter(
        (cb) => cb !== callback
      );
    };
  }

  public async getKeys(): Promise<any> {
    try {
      if (!this.token) {
        console.error("No authentication token available");
        return null;
      }

      const response = await fetch(`${this.pagosUrl}/api/v1/keys/`, {
        method: "GET",
        headers: {
          accept: "application/json",
          "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
          authorization: `Bearer ${this.token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.apiKey = data?.[0]?.api_key;
      return data;
    } catch (error) {
      console.error("Error fetching keys:", error);
      return null;
    }
  }

  public async getKeysUser(): Promise<any> {
    try {
      if (!this.token || !this.apiKey) {
        console.error("No authentication token available");
        return null;
      }

      const response = await fetch(
        `${this.pagosUrl}/api/v1/keys/user?api_key=${this.apiKey}`,
        {
          method: "GET",
          headers: {
            accept: "application/json",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            authorization: `Bearer ${this.token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return { data, token: this.token };
    } catch (error) {
      console.error("Error fetching keys user:", error);
      return null;
    }
  }

  public async logout() {
    await this.memberstack.logout();
    document.cookie = "_ms-mid" + "=;expires=Thu, 01 Jan 1970 00:00:01 GMT;";
  }

  private hideAppContent() {
    console.log("Hiding app content");
    const appContent = document.getElementById("root");
    if (appContent) {
      appContent.style.display = "none";
    }
  }

  private showAppContent() {
    console.log("Showing app content");
    const appContent = document.getElementById("root");
    if (appContent) {
      appContent.style.display = "block";
    }
  }

  private async checkAuthStatus() {
    try {
      const member = await this.memberstack.getMemberCookie();
      this.token = member;
      const newAuthState = !!member;
      if (this.isAuthenticated !== newAuthState) {
        this.isAuthenticated = newAuthState;
        this.notifyAuthStateChange();
      }
      if (member) {
        this.showAppContent();
        this.checkCredits();
        this.hideLoginModal();
      } else {
        this.hideAppContent();
        this.showLoginModal();
      }
      console.log("Auth status checked:", {
        member,
        isAuthenticated: this.isAuthenticated,
      });
    } catch (error) {
      console.error("Error checking auth status:", error);
      this.isAuthenticated = false;
      this.notifyAuthStateChange();
      this.showLoginModal();
      this.hideAppContent();
    }
  }

  private createLoginModal() {
    console.log("Creating login modal");
    // Remove any existing modal first
    const existingModal = document.getElementById("lyzr-login-modal-container");
    if (existingModal) {
      console.log("Removing existing modal");
      existingModal.remove();
    }

    const modalHtml = `
    <div id="lyzr-login-modal" style="
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(41, 41, 41, 0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 9999;
    ">
      <div style="
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(41, 41, 41, 0.1);
        width: 480px;
        max-width: 90vw;
        text-align: center;
        font-family: system-ui, -apple-system, sans-serif;
      ">
        <div style="
          display: flex; 
          justify-content: center; 
          margin-bottom: 32px;
        ">
          <img src="https://studio.lyzr.ai/images/Lyzr-Logo.svg" alt="Lyzr Logo" style="height: 40px;">
        </div>
        <button id="lyzr-studio-login" style="
          display: flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          margin-bottom: 16px;
          padding: 12px 24px;
          border: none;
          border-radius: 8px;
          background: #292929;
          color: white;
          font-size: 16px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        ">
          Sign In with Lyzr Agent Studio
        </button>
        <button id="lyzr-studio-signup" style="
          display: flex;
          align-items: center;
          justify-content: center;
          width: 100%;
          padding: 12px 24px;
          border: 1px solid #cacaca;
          border-radius: 8px;
          background: white;
          color: #292929;
          font-size: 16px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s ease;
        ">
          Sign Up with Lyzr Agent Studio
        </button>
      </div>
    </div>
  `;
    const modalElement = document.createElement("div");
    modalElement.id = "lyzr-login-modal-container";
    modalElement.innerHTML = modalHtml;
    document.body.appendChild(modalElement);
    console.log("Modal element created:", modalElement);

    // Get the modal element and store reference
    const modal = document.getElementById("lyzr-login-modal");
    if (!modal) {
      console.error("Failed to find modal element after creation");
      return;
    }
    this.modal = modal;
    console.log("Modal reference set:", this.modal);

    // Add Google login button click handler
    const googleButton = document.getElementById("lyzr-google-login");
    const studioButton = document.getElementById("lyzr-studio-login");
    const signupButton = document.getElementById("lyzr-studio-signup");
    if (googleButton) {
      googleButton.addEventListener("click", () => this.handleGoogleLogin());
    } else {
      console.error("Failed to find Google login button");
    }

    if (studioButton) {
      studioButton.addEventListener("click", () =>
        this.handleAgentStudioLogin()
      );
    } else {
      console.error("Failed to find  login button");
    }
    if (signupButton) {
      signupButton.addEventListener("click", () =>
        this.handleAgentStudioSignup()
      );
    } else {
      console.error("Failed to find signup button");
    }
  }

  private async handleGoogleLogin() {
    try {
      await this.memberstack.loginWithProvider({
        provider: "google",
      });
      await this.checkAuthStatus();
    } catch (error) {
      console.error("Error during Google login:", error);
    }
  }

  private handleAgentStudioLogin() {
    window.location.href = `${this.agentStudioUrl}/?redirect=${window.location.origin}`;
  }
  private handleAgentStudioSignup() {
    window.location.href = `${this.agentStudioUrlSignup}/?redirect=${window.location.origin}`;
  }

  private createBadge() {
    const badgeHtml = `
      <div id="lyzr-badge" style="
        position: fixed;
        ${this.badgePosition.x};
        ${this.badgePosition.y};
        background: white;
        padding: 8px 12px;
        border-radius: 6px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        font-family: system-ui, -apple-system, sans-serif;
        font-size: 14px;
        color: #333;
        display: flex;
        align-items: center;
        gap: 8px;
        z-index: 1000;
        cursor: pointer;
        transition: transform 0.2s ease;
      ">
        <span>Powered by Lyzr Agent Studio</span>
        <img src="https://studio.lyzr.ai/images/Lyzr-Logo.svg" alt="Lyzr Logo" style="height: 20px; width: auto;">
      </div>
    `;
    const badgeElement = document.createElement("div");
    badgeElement.innerHTML = badgeHtml;
    document.body.appendChild(badgeElement);
    this.badge = badgeElement.firstElementChild as HTMLElement;

    // Add click handler for the entire badge
    if (this.badge) {
      // Add hover effect
      this.badge.addEventListener("mouseover", () => {
        this.badge!.style.transform = "scale(1.02)";
      });
      this.badge.addEventListener("mouseout", () => {
        this.badge!.style.transform = "scale(1)";
      });

      // Add click handler to redirect to Lyzr Studio
      this.badge.addEventListener("click", () => {
        window.open("https://studio.lyzr.ai/", "_blank");
      });
    }
  }

  setBadgePosition(x?: string, y?: string) {
    console.warn(this.isAuthenticated);
    if (!this.isAuthenticated) {
      console.warn("User must be authenticated to modify badge position");
      return;
    }

    if (x) this.badgePosition.x = `right: ${x}`;
    if (y) this.badgePosition.y = `bottom: ${y}`;

    if (this.badge) {
      this.badge.style.right = x || "20px";
      this.badge.style.bottom = y || "20px";
    }
  }

  private showLoginModal() {
    console.log("Showing login modal");
    if (!this.modal) {
      console.warn("Modal not found, creating new one");
      this.createLoginModal();
    }

    if (this.modal) {
      console.log("Setting modal display to block");
      requestAnimationFrame(() => {
        if (this.modal) {
          this.modal.style.display = "block";
          console.log(
            "Modal display style after update:",
            this.modal.style.display
          );
          // Force a reflow
          this.modal.offsetHeight;
        }
      });
    } else {
      console.error("Failed to show modal");
    }
  }

  private hideLoginModal() {
    console.log("Hiding login modal");
    if (this.modal) {
      this.modal.style.display = "none";
    }
  }

  public async checkCredits(): Promise<void> {
    try {
      const response = await fetch(`${this.pagosUrl}/api/v1/usages/current`, {
        method: "GET",
        headers: {
          accept: "application/json",
          "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
          authorization: `Bearer ${this.token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const totalCredits =
        (data.recurring_credits || 0) +
        (data.paid_credits || 0) +
        (data.used_credits || 0);
      const usedCredits = data.used_credits || 0;
      const remainingCredits =
        (data.recurring_credits || 0) + (data.paid_credits || 0);

      if (remainingCredits <= 0) {
        this.showCreditErrorModal();
      } else if (remainingCredits <= 20) {
        this.showCreditWarningModal(remainingCredits);
      }
    } catch (error) {
      console.error("Error checking credits:", error);
    }
  }

  private createCreditErrorModal() {
    const modalHtml = `
      <div id="lyzr-credit-error-modal" style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: none;
        justify-content: center;
        align-items: center;
        z-index: 9999;
      ">
        <div style="
          position: relative;
          background: white;
          padding: 32px;
          border-radius: 16px;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
          width: 400px;
          text-align: center;
          font-family: system-ui, -apple-system, sans-serif;
        ">
          <div style="display: flex; justify-content: center; margin-bottom: 24px;">
            <img src="https://studio.lyzr.ai/images/Lyzr-Logo.svg" alt="Lyzr Logo" style="height: 40px;">
          </div>
          <h2 style="
            margin: 0 0 12px;
            color: #dc2626;
            font-size: 24px;
            font-weight: 600;
          ">Credits Exhausted</h2>
          <p style="
            margin: 0 0 24px;
            color: #666;
            font-size: 16px;
            line-height: 1.5;
          ">You've used all your available credits. Please recharge to continue using the service.</p>
           <div style="
            display: flex;
            gap: 12px;
          ">
            <button id="lyzr-credit-error-redirect" style="
              flex: 1;
              padding: 12px 24px;
              background:rgba(129, 64, 241, 0.75);
              color: white;
              border: none;
              border-radius: 8px;
              font-size: 16px;
              font-weight: 500;
              cursor: pointer;
              transition: all 0.2s ease;
            ">Get Credits</button>
            <button id="lyzr-logout-button" style="
              flex: 1;
              padding: 12px 12px;
              background: white;
        padding: 8px 12px;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
              color: black;
              border:2px;
              border-radius: 8px;
              font-size: 16px;
              font-weight: 500;
              cursor: pointer;
              transition: all 0.2s ease;
            ">Logout</button>
          </div>
        </div>
      </div>
    `;

    const modalElement = document.createElement("div");
    modalElement.innerHTML = modalHtml;
    document.body.appendChild(modalElement);
    this.creditErrorModal = modalElement.firstElementChild as HTMLElement;

    // Add event listeners
    const closeButton = document.getElementById("lyzr-credit-error-close");
    const redirectButton = document.getElementById(
      "lyzr-credit-error-redirect"
    );
    const logoutButton = document.getElementById("lyzr-logout-button");
    if (closeButton) {
      closeButton.addEventListener("click", () => this.hideCreditErrorModal());
    }

    if (redirectButton) {
      redirectButton.addEventListener("click", () => {
        window.open("https://studio.lyzr.ai/organization", "_blank");
      });
    }
    if (logoutButton) {
      logoutButton.addEventListener("click", async () => {
        await this.logout();
        this.hideCreditErrorModal();
      });
    }
  }

  private createCreditWarningModal() {
    const modalHtml = `
      <div id="lyzr-credit-warning-modal" style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: none;
        justify-content: center;
        align-items: center;
        z-index: 9999;
      ">
        <div style="
          position: relative;
          background: white;
          padding: 32px;
          border-radius: 16px;
          box-shadow: 0 4px 24px rgba(0, 0, 0, 0.1);
          width: 400px;
          text-align: center;
          font-family: system-ui, -apple-system, sans-serif;
        ">
          <button id="lyzr-credit-warning-close" style="
            position: absolute;
            top: 16px;
            right: 16px;
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            padding: 4px;
            color: #666;
          ">×</button>
          <img src="https://studio.lyzr.ai/images/Lyzr-Logo.svg" alt="Lyzr Logo" style="
            height: 40px;
            margin-bottom: 24px;
          ">
          <h2 style="
            margin: 0 0 12px;
            color: #f59e0b;
            font-size: 24px;
            font-weight: 600;
          ">Low Credits Warning</h2>
          <p id="lyzr-credit-warning-message" style="
            margin: 0 0 24px;
            color: #666;
            font-size: 16px;
            line-height: 1.5;
          ">Your credits are running low. Consider topping up to ensure uninterrupted service.</p>
          <div style="display: flex; gap: 12px;">
            <button id="lyzr-credit-warning-continue" style="
              flex: 1;
              padding: 12px 24px;
              background: #e5e7eb;
              color: #374151;
              border: none;
              border-radius: 8px;
              font-size: 16px;
              font-weight: 500;
              cursor: pointer;
              transition: all 0.2s ease;
            ">Continue</button>
            <button id="lyzr-credit-warning-redirect" style="
              flex: 1;
              padding: 12px 24px;
              background: #2563eb;
              color: white;
              border: none;
              border-radius: 8px;
              font-size: 16px;
              font-weight: 500;
              cursor: pointer;
              transition: all 0.2s ease;
            ">Top Up Now</button>
          </div>
        </div>
      </div>
    `;

    const modalElement = document.createElement("div");
    modalElement.innerHTML = modalHtml;
    document.body.appendChild(modalElement);
    this.creditWarningModal = modalElement.firstElementChild as HTMLElement;

    // Add event listeners
    const closeButton = document.getElementById("lyzr-credit-warning-close");
    const continueButton = document.getElementById(
      "lyzr-credit-warning-continue"
    );
    const redirectButton = document.getElementById(
      "lyzr-credit-warning-redirect"
    );

    if (closeButton) {
      closeButton.addEventListener("click", () =>
        this.hideCreditWarningModal()
      );
    }

    if (continueButton) {
      continueButton.addEventListener("click", () =>
        this.hideCreditWarningModal()
      );
    }

    if (redirectButton) {
      redirectButton.addEventListener("click", () => {
        window.open("https://studio.lyzr.ai/organization", "_blank");
      });
    }
  }

  private showCreditErrorModal() {
    if (!this.creditErrorModal) {
      this.createCreditErrorModal();
    }
    if (this.creditErrorModal) {
      this.creditErrorModal.style.display = "flex";
    }
  }

  private hideCreditErrorModal() {
    if (this.creditErrorModal) {
      this.creditErrorModal.style.display = "none";
    }
  }

  private showCreditWarningModal(remainingCredits: number) {
    if (!this.creditWarningModal) {
      this.createCreditWarningModal();
    }
    if (this.creditWarningModal) {
      const messageElement = document.getElementById(
        "lyzr-credit-warning-message"
      );
      if (messageElement) {
        messageElement.textContent = `You have ${remainingCredits} credits remaining. Consider topping up to ensure uninterrupted service.`;
      }
      this.creditWarningModal.style.display = "flex";
    }
  }

  private hideCreditWarningModal() {
    if (this.creditWarningModal) {
      this.creditWarningModal.style.display = "none";
    }
  }
}

// Create and export a single instance
const lyzrInstance = new LyzrAgent("pk_c14a2728e715d9ea67bf");

// Explicitly set as global
if (typeof window !== "undefined") {
  (window as any).lyzr = lyzrInstance;
}

export default lyzrInstance;
