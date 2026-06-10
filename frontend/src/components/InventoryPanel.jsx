import { RefreshCw, Snowflake } from "lucide-react";
import { daysUntil, formatDate, formatDateTime } from "../utils/format";
import { expirationTone, getFoodDisplayName, getFoodImageUrl } from "../utils/food";
import StatusBadge from "./StatusBadge";

export default function InventoryPanel({ foods, loading, message, onRefresh }) {
  return (
    <section className="panel inventory-panel">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Inventory</p>
          <h2>Fridge Matrix</h2>
        </div>
        <div className="heading-actions">
          <StatusBadge tone={loading ? "busy" : "ready"}>{loading ? "Syncing" : `${foods.length} items`}</StatusBadge>
          <button className="icon-button" type="button" onClick={onRefresh} disabled={loading} aria-label="Refresh inventory">
            <RefreshCw size={18} className={loading ? "spin" : ""} />
          </button>
        </div>
      </div>

      {message ? (
        <div className="empty-state">
          <Snowflake size={22} />
          <span>{message}</span>
        </div>
      ) : (
        <div className="inventory-grid">
          {foods.map((food) => (
            <FoodCard food={food} key={food.foodId || `${getFoodDisplayName(food)}-${food.createdAt}`} />
          ))}
        </div>
      )}
    </section>
  );
}

function FoodCard({ food }) {
  const imageUrl = getFoodImageUrl(food);
  const days = daysUntil(food.expirationDate);

  return (
    <article className={`food-card ${expirationTone(food)}`}>
      <div className="food-image">
        {imageUrl ? <img src={imageUrl} alt={getFoodDisplayName(food)} loading="lazy" /> : <Snowflake size={26} />}
      </div>
      <div className="food-info">
        <div>
          <h3>{getFoodDisplayName(food)}</h3>
          <p>{food.foodId || "No food id"}</p>
        </div>
        <dl>
          <div>
            <dt>Expires</dt>
            <dd>{formatDate(food.expirationDate)}</dd>
          </div>
          <div>
            <dt>Time left</dt>
            <dd>{days === null ? "Unknown" : days < 0 ? `${Math.abs(days)}d late` : `${days}d`}</dd>
          </div>
          <div>
            <dt>Captured</dt>
            <dd>{formatDateTime(food.foodImage?.capturedAt || food.createdAt)}</dd>
          </div>
        </dl>
      </div>
    </article>
  );
}
