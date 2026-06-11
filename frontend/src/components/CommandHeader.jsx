import { LogOut, Snowflake, UserRound } from "lucide-react";

export default function CommandHeader({ session, onSignOut }) {
  const userLabel = session.user.displayName || session.user.email;

  return (
    <header className="command-header">
      <div className="brand-mark">
        <Snowflake size={28} />
      </div>
      <div className="header-copy">
        <p className="eyebrow">Smart Fridge</p>
        <h1>FreshGuarGaurdilo's Stomach</h1>
      </div>
      <div className="header-status">
        {session.idToken && (
          <span className="user-pill">
            <UserRound size={15} />
            {userLabel}
          </span>
        )}
        {session.idToken && (
          <button className="icon-button" type="button" onClick={onSignOut} aria-label="Sign out">
            <LogOut size={18} />
          </button>
        )}
      </div>
    </header>
  );
}
