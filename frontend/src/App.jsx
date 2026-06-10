import { useCallback, useEffect, useState } from "react";
import { errorToObject } from "./api/http";
import { getDeviceState, listMyFoods } from "./api/smartFridgeApi";
import { clearSession, loadSession } from "./auth/sessionStore";
import AuthPanel from "./components/AuthPanel";
import CommandHeader from "./components/CommandHeader";
import DeviceStatePanel from "./components/DeviceStatePanel";
import FaceRegistrationPanel from "./components/FaceRegistrationPanel";
import InventoryPanel from "./components/InventoryPanel";
import PutFoodPanel from "./components/PutFoodPanel";
import ResultConsole from "./components/ResultConsole";
import RetrieveFoodPanel from "./components/RetrieveFoodPanel";

export default function App() {
  const isDevRoute = window.location.pathname.replace(/\/+$/, "") === "/dev";
  const [session, setSession] = useState(() => loadSession());
  const [foods, setFoods] = useState([]);
  const [inventoryMessage, setInventoryMessage] = useState(session.idToken ? "Loading inventory" : "");
  const [inventoryLoading, setInventoryLoading] = useState(false);
  const [deviceState, setDeviceState] = useState(null);
  const [deviceStateMessage, setDeviceStateMessage] = useState(session.idToken ? "Loading device state" : "");
  const [deviceStateLoading, setDeviceStateLoading] = useState(false);
  const [result, setResult] = useState({});

  const showResult = useCallback((value) => {
    setResult(value instanceof Error ? errorToObject(value) : value);
  }, []);

  const loadInventory = useCallback(async () => {
    if (!session.idToken) {
      setFoods([]);
      setInventoryMessage("");
      return;
    }

    setInventoryLoading(true);
    setInventoryMessage("Loading inventory");
    try {
      const response = await listMyFoods(session.idToken);
      const nextFoods = response.foods || [];
      setFoods(nextFoods);
      setInventoryMessage(nextFoods.length ? "" : "No foods in fridge");
    } catch (error) {
      setFoods([]);
      setInventoryMessage(error.message || "Unable to load inventory");
      showResult(error);
    } finally {
      setInventoryLoading(false);
    }
  }, [session.idToken, showResult]);

  const loadDeviceState = useCallback(async () => {
    if (!session.idToken) {
      setDeviceState(null);
      setDeviceStateMessage("");
      return;
    }

    setDeviceStateLoading(true);
    setDeviceStateMessage("Loading device state");
    try {
      const response = await getDeviceState(session.idToken);
      setDeviceState(response);
      setDeviceStateMessage("");
    } catch (error) {
      setDeviceState(null);
      setDeviceStateMessage(error.message || "Unable to load device state");
      showResult(error);
    } finally {
      setDeviceStateLoading(false);
    }
  }, [session.idToken, showResult]);

  useEffect(() => {
    void loadInventory();
  }, [loadInventory]);

  useEffect(() => {
    void loadDeviceState();
  }, [loadDeviceState]);

  function handleSessionChange(nextSession) {
    if (!nextSession) {
      clearSession();
      setSession(loadSession());
      setFoods([]);
      setInventoryMessage("");
      setDeviceState(null);
      setDeviceStateMessage("");
      setResult({ success: true, signedOut: true });
      return;
    }

    setSession(nextSession);
  }

  return (
    <main className="app-shell">
      <CommandHeader session={session} onSignOut={() => handleSessionChange(null)} />

      {session.idToken ? (
        <section className={isDevRoute ? "dashboard-grid" : "home-grid"}>
          <FaceRegistrationPanel session={session} onResult={showResult} />
          <InventoryPanel foods={foods} loading={inventoryLoading} message={inventoryMessage} onRefresh={loadInventory} />
          <DeviceStatePanel deviceState={deviceState} loading={deviceStateLoading} message={deviceStateMessage} onRefresh={loadDeviceState} />
          {isDevRoute && (
            <>
              <PutFoodPanel session={session} onInventoryChanged={loadInventory} onResult={showResult} />
              <RetrieveFoodPanel session={session} onInventoryChanged={loadInventory} onResult={showResult} />
              <ResultConsole value={result} onClear={() => setResult({})} />
            </>
          )}
        </section>
      ) : (
        <section className="auth-layout">
          <AuthPanel onSessionChange={handleSessionChange} onResult={showResult} />
        </section>
      )}
    </main>
  );
}
