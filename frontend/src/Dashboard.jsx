import { useState, useEffect, useRef } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";

// Karina's real data 
import LOCATIONS from './locations.json';

const CAMERAS = [
  { name: "I-66 & Route 50", location: "Arlington VA", lat: 38.8816, lon: -77.1003, status: "congested" },
  { name: "I-395 & Route 1", location: "Arlington VA", lat: 38.851, lon: -77.0502, status: "heavy" },
  { name: "Route 7 & Glebe Rd", location: "Arlington VA", lat: 38.8868, lon: -77.1172, status: "normal" },
  { name: "I-66 & Sycamore St", location: "Arlington VA", lat: 38.8793, lon: -77.1189, status: "normal" },
  { name: "Route 50 & George Mason Dr", location: "Arlington VA", lat: 38.8709, lon: -77.1094, status: "congested" },
  { name: "I-495 & Route 7", location: "Tysons VA", lat: 38.9182, lon: -77.2277, status: "normal" },
  { name: "I-95 & Route 123", location: "Woodbridge VA", lat: 38.6543, lon: -77.2511, status: "normal" },
  { name: "Route 28 & Centreville Rd", location: "Manassas VA", lat: 38.751, lon: -77.4629, status: "normal" },
];

const WEATHER_ALERTS = [
  {
    event: "Special Weather Statement",
    headline: "Special Weather Statement issued March 28 at 5:11AM EDT by NWS Baltimore MD/Washington DC",
    severity: "Moderate",
    area: "DC · Arlington · Fairfax · Falls Church · Alexandria",
  },
  {
    event: "Freeze Warning",
    headline: "Freeze Warning issued March 28 at 1:08PM EDT until March 29 at 10:00AM EDT by NWS Charleston WV",
    severity: "Moderate",
    area: "Western VA counties",
  },
];

//  Pretend NLP output (Jake's model, need to swap schema here when he responds) 
const NLP_ALERTS = [
  {
    id: "nlp-001",
    timestamp: "2026-04-09T14:18:00Z",
    type: "fuel",
    severity: "high",
    location: { lat: 38.8816, lon: -77.1074, label: "Arlington, VA — I-66 corridor" },
    sentiment_score: -0.87,
    confidence: 0.91,
    source_text: "Gas stations running completely dry along Route 50, lines stretching 2 blocks",
    signals: 3,
    disruption_detected: true,
  },
  {
    id: "nlp-002",
    timestamp: "2026-04-09T13:45:00Z",
    type: "food",
    severity: "medium",
    location: { lat: 38.9182, lon: -77.2277, label: "Tysons, VA — supply delay" },
    sentiment_score: -0.54,
    confidence: 0.78,
    source_text: "Giant and Safeway shelves emptying fast, restocking trucks not arriving",
    signals: 2,
    disruption_detected: true,
  },
  {
    id: "nlp-003",
    timestamp: "2026-04-09T13:22:00Z",
    type: "fuel",
    severity: "high",
    location: { lat: 38.851, lon: -77.0502, label: "I-395 & Route 1 — congestion" },
    sentiment_score: -0.79,
    confidence: 0.85,
    source_text: "I-395 completely gridlocked, fuel delivery trucks stuck for hours",
    signals: 3,
    disruption_detected: true,
  },
  {
    id: "nlp-004",
    timestamp: "2026-04-09T11:08:00Z",
    type: "food",
    severity: "low",
    location: { lat: 38.8648, lon: -77.1022, label: "Alexandria — weather advisory" },
    sentiment_score: -0.21,
    confidence: 0.62,
    source_text: "Some delays reported at local grocery stores due to icy roads",
    signals: 1,
    disruption_detected: true,
  },
];

const C = {
  bg: "#0f1623",
  surface: "#131c2e",
  surface2: "#1a2540",
  border: "#1e2d45",
  text: "#e2e8f0",
  muted: "#64748b",
  dim: "#334155",
  red: "#ef4444",
  redBg: "#7f1d1d",
  redText: "#fca5a5",
  amber: "#f59e0b",
  amberBg: "#78350f",
  amberText: "#fcd34d",
  green: "#10b981",
  greenBg: "#064e3b",
  greenText: "#6ee7b7",
  blue: "#3b82f6",
  blueBg: "#1e3a5f",
  blueText: "#93c5fd",
  font: "'IBM Plex Mono', 'Courier New', monospace",
  fontSans: "'DM Sans', system-ui, sans-serif",
};


const severityColor = (s) =>
  s === "high" ? C.red : s === "medium" ? C.amber : C.green;

const severityBg = (s) =>
  s === "high" ? C.redBg : s === "medium" ? C.amberBg : C.greenBg;

const severityText = (s) =>
  s === "high" ? C.redText : s === "medium" ? C.amberText : C.greenText;

const cameraStatusColor = (s) =>
  s === "heavy" ? C.red : s === "congested" ? C.amber : C.green;

const formatTime = (iso) => {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", timeZoneName: "short" });
};

const sentScore = (score) => Math.round(Math.abs(score) * 100);

function LowBandwidthView({ alerts, weather, onExit }) {
  return (
    <div style={{ background: "#000", color: "#00ff00", fontFamily: C.font, fontSize: 13, padding: 16, minHeight: "100vh" }}>
      <div style={{ borderBottom: "1px solid #00ff00", paddingBottom: 8, marginBottom: 12 }}>
        <div style={{ fontSize: 11, opacity: 0.6 }}>LOW BANDWIDTH MODE — CNA SUPPLY CHAIN MONITOR</div>
        <div style={{ fontSize: 10, opacity: 0.4 }}>DC/NoVA · {new Date().toLocaleTimeString()}</div>
      </div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ color: "#ffff00", marginBottom: 6, fontSize: 11 }}>▶ ACTIVE ALERTS ({alerts.filter(a => a.disruption_detected).length})</div>
        {alerts.map((a, i) => (
          <div key={i} style={{ marginBottom: 8, paddingLeft: 8, borderLeft: `2px solid ${severityColor(a.severity)}` }}>
            <div style={{ color: severityColor(a.severity), fontSize: 12, fontWeight: "bold" }}>
              [{a.severity.toUpperCase()}] {a.location.label}
            </div>
            <div style={{ fontSize: 11, opacity: 0.8 }}>Type: {a.type} · Score: {a.sentiment_score} · Confidence: {Math.round(a.confidence * 100)}%</div>
            <div style={{ fontSize: 10, opacity: 0.6 }}>"{a.source_text.substring(0, 80)}..."</div>
          </div>
        ))}
      </div>
      <div style={{ marginBottom: 12 }}>
        <div style={{ color: "#ffff00", marginBottom: 6, fontSize: 11 }}>▶ WEATHER ({weather.length})</div>
        {weather.map((w, i) => (
          <div key={i} style={{ marginBottom: 6, fontSize: 11, opacity: 0.9 }}>
            [{w.severity.toUpperCase()}] {w.event} — {w.area}
          </div>
        ))}
      </div>
      <button
        onClick={onExit}
        style={{ background: "transparent", border: "1px solid #00ff00", color: "#00ff00", fontFamily: C.font, fontSize: 11, padding: "4px 12px", cursor: "pointer", marginTop: 8 }}
      >
        ← EXIT LOW BANDWIDTH MODE
      </button>
    </div>
  );
}

function FatigueBanner({ sessionMinutes }) {
  if (sessionMinutes < 360) return null;
  const hours = Math.floor(sessionMinutes / 60);
  return (
    <div style={{
      background: C.amberBg, borderBottom: `1px solid ${C.amber}`, padding: "6px 16px",
      display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 11, fontFamily: C.font,
    }}>
      <span style={{ color: C.amberText }}>
        ⚠ FATIGUE ALERT — Active session: {hours}h. Consider rotating with another operator.
      </span>
      <span style={{ color: C.amber, opacity: 0.7 }}>Recommend hand-off</span>
    </div>
  );
}

function MapController({ center }) {
  const map = useMap();
  useEffect(() => { map.setView(center, map.getZoom()); }, [center]);
  return null;
}

export default function Dashboard() {
  const [layers, setLayers] = useState({ fuel: true, food: true, cameras: true, alerts: true, weather: false });
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [lowBandwidth, setLowBandwidth] = useState(false);
  const [sessionMinutes, setSessionMinutes] = useState(0);
  const [mapCenter] = useState([38.88, -77.1]);
  const sessionRef = useRef(null);

  useEffect(() => {
    sessionRef.current = setInterval(() => setSessionMinutes(m => m + 1), 60000);
    return () => clearInterval(sessionRef.current);
  }, []);

  const toggleLayer = (key) => setLayers(l => ({ ...l, [key]: !l[key] }));

  const highAlerts = NLP_ALERTS.filter(a => a.severity === "high").length;
  const fuelNeg = Math.round(Math.abs(NLP_ALERTS.filter(a => a.type === "fuel").reduce((s, a) => s + a.sentiment_score, 0) / NLP_ALERTS.filter(a => a.type === "fuel").length) * 100);
  const foodNeg = Math.round(Math.abs(NLP_ALERTS.filter(a => a.type === "food").reduce((s, a) => s + a.sentiment_score, 0) / NLP_ALERTS.filter(a => a.type === "food").length) * 100);

  if (lowBandwidth) return <LowBandwidthView alerts={NLP_ALERTS} weather={WEATHER_ALERTS} onExit={() => setLowBandwidth(false)} />;

  return (
    <div style={{ fontFamily: C.fontSans, background: C.bg, color: C.text, height: "100vh", display: "flex", flexDirection: "column", overflow: "hidden" }}>
      <div style={{ background: C.surface, borderBottom: `1px solid ${C.border}`, padding: "0 16px", height: 48, display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 28, height: 28, background: C.blueBg, borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14 }}>🛡</div>
          <span style={{ fontFamily: C.font, fontSize: 13, fontWeight: "bold", letterSpacing: 1, color: C.text }}>CNA SUPPLY CHAIN MONITOR</span>
          <span style={{ background: C.redBg, color: C.redText, fontSize: 10, padding: "2px 8px", borderRadius: 4, fontFamily: C.font, letterSpacing: 1 }}>LIVE</span>
          <span style={{ background: C.blueBg, color: C.blueText, fontSize: 10, padding: "2px 8px", borderRadius: 4, fontFamily: C.font }}>DC / NoVA</span>
          {highAlerts > 0 && (
            <span style={{ background: C.redBg, color: C.redText, fontSize: 10, padding: "2px 8px", borderRadius: 4, fontFamily: C.font }}>
              {highAlerts} HIGH SEVERITY
            </span>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 11, color: C.muted, fontFamily: C.font }}>
            Session: {sessionMinutes}m
          </span>
          <span style={{ fontSize: 11, color: C.muted, fontFamily: C.font }}>
            {new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", timeZoneName: "short" })}
          </span>
          <button
            onClick={() => setLowBandwidth(true)}
            style={{ background: "transparent", border: `1px solid ${C.dim}`, color: C.muted, fontFamily: C.font, fontSize: 10, padding: "4px 10px", borderRadius: 4, cursor: "pointer", letterSpacing: 1 }}
          >
            LOW BW MODE
          </button>
        </div>
      </div>

      <FatigueBanner sessionMinutes={sessionMinutes} />

      <div style={{ display: "grid", gridTemplateColumns: "240px 1fr 240px", flex: 1, overflow: "hidden" }}>

        <div style={{ background: C.surface, borderRight: `1px solid ${C.border}`, display: "flex", flexDirection: "column", overflow: "hidden" }}>

          <div style={{ padding: "8px 8px 0", borderBottom: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 9, color: C.muted, fontFamily: C.font, letterSpacing: 1, padding: "4px 4px 6px" }}>SUPPLY CHAIN STATUS</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, paddingBottom: 10 }}>
              {[
                { label: "Fuel sites", val: LOCATIONS.filter(l => l.type === "fuel").length, color: C.amber },
                { label: "Food sites", val: LOCATIONS.filter(l => l.type === "supermarket").length, color: C.green },
                { label: "High alerts", val: highAlerts, color: C.red },
                { label: "Cameras", val: CAMERAS.length, color: C.blue },
              ].map((m, i) => (
                <div key={i} style={{ background: C.surface2, borderRadius: 6, padding: "8px 10px", border: `1px solid ${C.border}` }}>
                  <div style={{ fontSize: 9, color: C.muted, fontFamily: C.font, letterSpacing: .5, marginBottom: 4 }}>{m.label.toUpperCase()}</div>
                  <div style={{ fontSize: 22, fontWeight: 600, color: m.color, fontFamily: C.font }}>{m.val}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ fontSize: 9, color: C.muted, fontFamily: C.font, letterSpacing: 1, padding: "8px 12px 4px" }}>ACTIVE ALERTS</div>
          <div style={{ flex: 1, overflowY: "auto" }}>
            {NLP_ALERTS.map((a) => (
              <div
                key={a.id}
                onClick={() => setSelectedAlert(selectedAlert?.id === a.id ? null : a)}
                style={{
                  padding: "10px 12px",
                  borderBottom: `1px solid ${C.border}`,
                  cursor: "pointer",
                  background: selectedAlert?.id === a.id ? C.surface2 : "transparent",
                  borderLeft: selectedAlert?.id === a.id ? `3px solid ${severityColor(a.severity)}` : "3px solid transparent",
                  transition: "all 0.15s",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 3 }}>
                  <div style={{ width: 7, height: 7, borderRadius: "50%", background: severityColor(a.severity), flexShrink: 0 }} />
                  <span style={{ fontSize: 11, fontWeight: 600, color: C.text }}>{a.location.label}</span>
                </div>
                <div style={{ fontSize: 10, color: C.muted, marginLeft: 13, marginBottom: 4, lineHeight: 1.4 }}>
                  {a.source_text.substring(0, 65)}...
                </div>
                <div style={{ display: "flex", gap: 6, marginLeft: 13 }}>
                  <span style={{ fontSize: 9, background: severityBg(a.severity), color: severityText(a.severity), padding: "1px 6px", borderRadius: 3, fontFamily: C.font }}>
                    {a.severity.toUpperCase()}
                  </span>
                  <span style={{ fontSize: 9, background: C.surface2, color: C.muted, padding: "1px 6px", borderRadius: 3, fontFamily: C.font }}>
                    {a.type.toUpperCase()}
                  </span>
                  <span style={{ fontSize: 9, color: C.dim, fontFamily: C.font, marginLeft: "auto" }}>
                    {formatTime(a.timestamp)}
                  </span>
                </div>
                {selectedAlert?.id === a.id && (
                  <div style={{ marginTop: 8, marginLeft: 13, padding: 8, background: C.bg, borderRadius: 4, border: `1px solid ${C.border}` }}>
                    <div style={{ fontSize: 10, color: C.muted, fontFamily: C.font, marginBottom: 4 }}>NLP ANALYSIS</div>
                    <div style={{ fontSize: 10, color: C.text, marginBottom: 3 }}>
                      Sentiment: <span style={{ color: C.red, fontFamily: C.font }}>{a.sentiment_score}</span>
                    </div>
                    <div style={{ fontSize: 10, color: C.text, marginBottom: 3 }}>
                      Confidence: <span style={{ color: C.green, fontFamily: C.font }}>{Math.round(a.confidence * 100)}%</span>
                    </div>
                    <div style={{ fontSize: 10, color: C.text }}>
                      Signals: <span style={{ color: C.amber, fontFamily: C.font }}>{a.signals} converging</span>
                    </div>
                    <div style={{ fontSize: 9, color: C.muted, marginTop: 6, fontStyle: "italic", lineHeight: 1.4 }}>
                      "{a.source_text}"
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div style={{ position: "relative" }}>
          <MapContainer
            center={mapCenter}
            zoom={11}
            style={{ height: "100%", width: "100%", background: C.bg }}
            zoomControl={false}
          >
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            />
            <MapController center={mapCenter} />

            {layers.fuel && LOCATIONS.filter(l => l.type === "fuel").map((loc, i) => (
              <CircleMarker key={`fuel-${i}`} center={[loc.lat, loc.lon]} radius={5}
                pathOptions={{ color: C.amber, fillColor: C.amber, fillOpacity: 0.8, weight: 1 }}>
                <Popup>
                  <div style={{ fontFamily: C.fontSans, fontSize: 12 }}>
                    <strong>{loc.name}</strong><br />
                    <span style={{ color: "#888" }}>Fuel station</span><br />
                    {loc.lat.toFixed(4)}, {loc.lon.toFixed(4)}
                  </div>
                </Popup>
              </CircleMarker>
            ))}

            {layers.food && LOCATIONS.filter(l => l.type === "supermarket").map((loc, i) => (
              <CircleMarker key={`food-${i}`} center={[loc.lat, loc.lon]} radius={5}
                pathOptions={{ color: C.green, fillColor: C.green, fillOpacity: 0.8, weight: 1 }}>
                <Popup>
                  <div style={{ fontFamily: C.fontSans, fontSize: 12 }}>
                    <strong>{loc.name}</strong><br />
                    <span style={{ color: "#888" }}>Supermarket</span>
                  </div>
                </Popup>
              </CircleMarker>
            ))}

            {layers.cameras && CAMERAS.map((cam, i) => (
              <CircleMarker key={`cam-${i}`} center={[cam.lat, cam.lon]} radius={5}
                pathOptions={{ color: C.blue, fillColor: C.blue, fillOpacity: 0.7, weight: 1 }}>
                <Popup>
                  <div style={{ fontFamily: C.fontSans, fontSize: 12 }}>
                    <strong>{cam.name}</strong><br />
                    <span style={{ color: "#888" }}>{cam.location}</span><br />
                    Status: <strong style={{ color: cameraStatusColor(cam.status) }}>{cam.status}</strong>
                  </div>
                </Popup>
              </CircleMarker>
            ))}

            {layers.alerts && NLP_ALERTS.filter(a => a.disruption_detected).map((a) => (
              <CircleMarker key={a.id} center={[a.location.lat, a.location.lon]}
                radius={a.severity === "high" ? 14 : 10}
                pathOptions={{ color: severityColor(a.severity), fillColor: severityColor(a.severity), fillOpacity: 0.25, weight: 2 }}>
                <Popup>
                  <div style={{ fontFamily: C.fontSans, fontSize: 12, maxWidth: 220 }}>
                    <div style={{ fontWeight: 700, marginBottom: 4 }}>{a.location.label}</div>
                    <div style={{ color: severityColor(a.severity), fontSize: 11, marginBottom: 4 }}>
                      {a.severity.toUpperCase()} — {a.type.toUpperCase()} DISRUPTION
                    </div>
                    <div style={{ fontSize: 11, color: "#555", marginBottom: 6 }}>"{a.source_text}"</div>
                    <div style={{ fontSize: 10, color: "#888" }}>
                      Sentiment: {a.sentiment_score} · Confidence: {Math.round(a.confidence * 100)}%
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>

          <div style={{ position: "absolute", top: 12, left: 12, zIndex: 1000, display: "flex", flexDirection: "column", gap: 4 }}>
            {[
              { key: "fuel", label: "⛽ Fuel", color: C.amber },
              { key: "food", label: "🛒 Food", color: C.green },
              { key: "cameras", label: "📷 Cameras", color: C.blue },
              { key: "alerts", label: "🔴 Alerts", color: C.red },
            ].map(({ key, label, color }) => (
              <button
                key={key}
                onClick={() => toggleLayer(key)}
                style={{
                  background: layers[key] ? C.surface2 : C.surface,
                  border: `1px solid ${layers[key] ? color : C.border}`,
                  color: layers[key] ? color : C.muted,
                  fontFamily: C.font, fontSize: 10, padding: "5px 10px",
                  borderRadius: 4, cursor: "pointer", textAlign: "left",
                  transition: "all 0.15s", letterSpacing: .5,
                }}
              >
                {label}
              </button>
            ))}
          </div>

          <div style={{ position: "absolute", bottom: 12, left: 12, zIndex: 1000, background: "rgba(15,22,35,0.92)", border: `1px solid ${C.border}`, borderRadius: 6, padding: "8px 12px" }}>
            {[
              { color: C.red, label: "Active disruption alert" },
              { color: C.amber, label: "Fuel station" },
              { color: C.green, label: "Food / grocery" },
              { color: C.blue, label: "Traffic camera" },
            ].map(({ color, label }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 10, color: C.muted, marginBottom: 3 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
                {label}
              </div>
            ))}
          </div>
        </div>

        <div style={{ background: C.surface, borderLeft: `1px solid ${C.border}`, display: "flex", flexDirection: "column", overflow: "hidden" }}>

          <div style={{ borderBottom: `1px solid ${C.border}`, padding: "8px 12px 12px" }}>
            <div style={{ fontSize: 9, color: C.muted, fontFamily: C.font, letterSpacing: 1, marginBottom: 8 }}>NLP SENTIMENT ANALYSIS</div>
            {[
              { label: "Fuel supply — negative signal", pct: fuelNeg, color: C.red },
              { label: "Food supply — negative signal", pct: foodNeg, color: C.amber },
            ].map(({ label, pct, color }) => (
              <div key={label} style={{ marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: C.muted, marginBottom: 4 }}>
                  <span>{label}</span>
                  <span style={{ color, fontFamily: C.font }}>{pct}%</span>
                </div>
                <div style={{ height: 5, background: C.surface2, borderRadius: 3, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 3, transition: "width 0.5s" }} />
                </div>
              </div>
            ))}
            <div style={{ fontSize: 9, color: C.dim, fontFamily: C.font, marginTop: 4 }}>
              Source: CrisisMMD · {NLP_ALERTS.length} posts analyzed
            </div>
          </div>

          <div style={{ borderBottom: `1px solid ${C.border}` }}>
            <div style={{ fontSize: 9, color: C.muted, fontFamily: C.font, letterSpacing: 1, padding: "8px 12px 4px" }}>WEATHER ALERTS</div>
            {WEATHER_ALERTS.map((w, i) => (
              <div key={i} style={{ padding: "8px 12px", borderBottom: i < WEATHER_ALERTS.length - 1 ? `1px solid ${C.border}` : "none" }}>
                <div style={{ fontSize: 11, color: C.amberText, fontWeight: 600, marginBottom: 2 }}>{w.event}</div>
                <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.4 }}>{w.area}</div>
              </div>
            ))}
          </div>

          <div style={{ borderBottom: `1px solid ${C.border}`, flex: 1, overflowY: "auto" }}>
            <div style={{ fontSize: 9, color: C.muted, fontFamily: C.font, letterSpacing: 1, padding: "8px 12px 4px" }}>
              TRAFFIC CAMERAS — {CAMERAS.length} FEEDS
            </div>
            {CAMERAS.map((cam, i) => (
              <div key={i} style={{ padding: "7px 12px", borderBottom: `1px solid ${C.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  <div style={{ fontSize: 11, color: C.text }}>{cam.name}</div>
                  <div style={{ fontSize: 10, color: C.muted }}>{cam.location}</div>
                </div>
                <div style={{ width: 7, height: 7, borderRadius: "50%", background: cameraStatusColor(cam.status), flexShrink: 0 }} />
              </div>
            ))}
          </div>

          <div style={{ padding: "8px 12px" }}>
            <div style={{ fontSize: 9, color: C.muted, fontFamily: C.font, letterSpacing: 1, marginBottom: 6 }}>DATA LAYERS</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {Object.keys(layers).map((key) => (
                <button
                  key={key}
                  onClick={() => toggleLayer(key)}
                  style={{
                    background: layers[key] ? C.blueBg : "transparent",
                    border: `1px solid ${layers[key] ? C.blue : C.dim}`,
                    color: layers[key] ? C.blueText : C.muted,
                    fontFamily: C.font, fontSize: 9, padding: "3px 8px",
                    borderRadius: 3, cursor: "pointer", letterSpacing: .5,
                    transition: "all 0.15s",
                  }}
                >
                  {key.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
