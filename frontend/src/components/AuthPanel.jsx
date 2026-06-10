import { ArrowLeft, KeyRound, LogIn, MailCheck, UserPlus } from "lucide-react";
import { useState } from "react";
import { confirmSignup, loginWithPassword, resendConfirmationCode } from "../api/cognitoApi";
import { signupUser } from "../api/smartFridgeApi";
import { getPendingEmail, saveSession, setPendingEmail } from "../auth/sessionStore";

export default function AuthPanel({ onSessionChange, onResult }) {
  const [mode, setMode] = useState("login");
  const [busy, setBusy] = useState("");
  const [signup, setSignup] = useState({ email: "", displayName: "", password: "" });
  const [confirm, setConfirm] = useState({ email: getPendingEmail(), code: "" });
  const [login, setLogin] = useState({ email: "", password: "" });
  const [notice, setNotice] = useState("");

  function publish(value) {
    onResult(value);
    if (value instanceof Error) {
      setNotice(value.payload?.message || value.message || "Request failed");
      return;
    }
    setNotice(value.message || (value.success === false ? "Request failed" : "Ready"));
  }

  function switchMode(nextMode) {
    setMode(nextMode);
    setNotice("");
  }

  async function handleSignup(event) {
    event.preventDefault();
    setBusy("signup");
    try {
      const response = await signupUser({
        username: signup.email.trim(),
        email: signup.email.trim(),
        password: signup.password,
        displayName: signup.displayName.trim()
      });
      setPendingEmail(signup.email.trim());
      setConfirm((current) => ({ ...current, email: signup.email.trim() }));
      setLogin((current) => ({ ...current, email: signup.email.trim() }));
      switchMode("confirm");
      publish(response);
    } catch (error) {
      publish(error);
    } finally {
      setBusy("");
    }
  }

  async function handleConfirm(event) {
    event.preventDefault();
    setBusy("confirm");
    try {
      const response = await confirmSignup({
        username: confirm.email.trim(),
        confirmationCode: confirm.code.trim()
      });
      switchMode("login");
      publish({ success: true, confirmed: true, message: "Account confirmed. You can sign in now.", ...response });
    } catch (error) {
      publish(error);
    } finally {
      setBusy("");
    }
  }

  async function handleResend() {
    const username = confirm.email.trim() || signup.email.trim() || getPendingEmail();
    if (!username) {
      publish({ success: false, errorCode: "NO_USERNAME", message: "Enter an email first" });
      return;
    }

    setBusy("resend");
    try {
      publish({ success: true, message: "Confirmation code sent.", ...(await resendConfirmationCode(username)) });
    } catch (error) {
      publish(error);
    } finally {
      setBusy("");
    }
  }

  async function handleLogin(event) {
    event.preventDefault();
    setBusy("login");
    try {
      const response = await loginWithPassword({
        email: login.email.trim(),
        password: login.password
      });
      const nextSession = saveSession({
        authenticationResult: response.AuthenticationResult,
        email: login.email.trim()
      });
      onSessionChange(nextSession);
      publish({
        success: true,
        email: nextSession.user.email,
        tokenType: response.AuthenticationResult.TokenType,
        expiresIn: response.AuthenticationResult.ExpiresIn
      });
    } catch (error) {
      publish(error);
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="panel auth-panel auth-gate">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Identity Required</p>
          <h2>{mode === "login" ? "Sign in" : mode === "signup" ? "Create account" : "Confirm account"}</h2>
        </div>
      </div>

      {mode === "login" && (
        <form className="form-grid" onSubmit={handleLogin}>
          <label className="wide-field">
            Email
            <input
              type="email"
              autoComplete="email"
              required
              value={login.email}
              onChange={(event) => setLogin({ ...login, email: event.target.value })}
            />
          </label>
          <label className="wide-field">
            Password
            <input
              type="password"
              autoComplete="current-password"
              required
              value={login.password}
              onChange={(event) => setLogin({ ...login, password: event.target.value })}
            />
          </label>
          <button className="ghost-button" type="button" disabled={Boolean(busy)} onClick={() => switchMode("signup")}>
            <UserPlus size={18} />
            Create account
          </button>
          <button type="submit" disabled={Boolean(busy)}>
            <LogIn size={18} />
            {busy === "login" ? "Signing in" : "Sign in"}
          </button>
        </form>
      )}

      {mode === "signup" && (
        <form className="form-grid" onSubmit={handleSignup}>
          <label className="wide-field">
            Email
            <input
              type="email"
              autoComplete="email"
              required
              value={signup.email}
              onChange={(event) => setSignup({ ...signup, email: event.target.value })}
            />
          </label>
          <label className="wide-field">
            Display name
            <input
              type="text"
              autoComplete="name"
              value={signup.displayName}
              onChange={(event) => setSignup({ ...signup, displayName: event.target.value })}
            />
          </label>
          <label className="wide-field">
            Password
            <input
              type="password"
              autoComplete="new-password"
              required
              value={signup.password}
              onChange={(event) => setSignup({ ...signup, password: event.target.value })}
            />
            <small>8+ chars, uppercase, lowercase, number</small>
          </label>
          <button className="ghost-button" type="button" disabled={Boolean(busy)} onClick={() => switchMode("login")}>
            <ArrowLeft size={18} />
            Back to sign in
          </button>
          <button type="submit" disabled={Boolean(busy)}>
            <UserPlus size={18} />
            {busy === "signup" ? "Creating" : "Create"}
          </button>
        </form>
      )}

      {mode === "confirm" && (
        <form className="form-grid" onSubmit={handleConfirm}>
          <label className="wide-field">
            Email
            <input
              type="email"
              value={confirm.email}
              onChange={(event) => setConfirm({ ...confirm, email: event.target.value })}
            />
          </label>
          <label className="wide-field">
            Code
            <input
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              value={confirm.code}
              onChange={(event) => setConfirm({ ...confirm, code: event.target.value })}
            />
          </label>
          <button type="submit" disabled={Boolean(busy)}>
            <MailCheck size={18} />
            {busy === "confirm" ? "Confirming" : "Confirm"}
          </button>
          <button className="ghost-button" type="button" disabled={Boolean(busy)} onClick={handleResend}>
            <KeyRound size={18} />
            {busy === "resend" ? "Sending" : "Resend"}
          </button>
          <button className="ghost-button wide-field" type="button" disabled={Boolean(busy)} onClick={() => switchMode("login")}>
            <ArrowLeft size={18} />
            Back to sign in
          </button>
        </form>
      )}

      {notice && <div className="auth-message">{notice}</div>}
    </section>
  );
}
