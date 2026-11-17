import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix pentru iconițele de Marker în Leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Puncte de livrare în Brașov
const deliveryPoints = [
  { id: 0, name: "Depozit Central (Start)", lat: 45.6579, lon: 25.6012, tw: "08:00 - 18:00" },
  { id: 1, name: "Client 1 - Coresi Mall", lat: 45.6725, lon: 25.6148, tw: "09:00 - 10:30" },
  { id: 2, name: "Client 2 - Gara Brașov", lat: 45.6611, lon: 25.6133, tw: "10:00 - 11:30" },
  { id: 3, name: "Client 3 - Piața Sfatului", lat: 45.6422, lon: 25.5889, tw: "11:00 - 12:30" },
  { id: 4, name: "Client 4 - Cartier Astra", lat: 45.6365, lon: 25.6320, tw: "12:00 - 14:00" },
];

export default function App() {
  const [selectedAlgo, setSelectedAlgo] = useState("ACO");
  const [metrics, setMetrics] = useState({
    distance: "13.2 km",
    time: "32 min",
    execTime: "1.42 sec",
    twCompliance: "4 / 4 (100%)"
  });

  const handleRunAlgorithm = () => {
    if (selectedAlgo.includes("ACO") || selectedAlgo.includes("GA")) {
      setMetrics({ distance: "13.2 km", time: "32 min", execTime: "1.42 sec", twCompliance: "4 / 4 (100%)" });
    } else {
      setMetrics({ distance: "14.9 km", time: "38 min", execTime: "0.01 sec", twCompliance: "3 / 4 (75%)" });
    }
  };

  const polylineCoords = deliveryPoints.map(p => [p.lat, p.lon]);
  polylineCoords.push([deliveryPoints[0].lat, deliveryPoints[0].lon]);

  return (
    <div className="flex w-screen h-screen bg-[#16171d] text-[#9ca3af] overflow-hidden m-0 p-0">

      {/* SIDEBAR STÂNGA (Fix pe lățime de 360px, înălțime 100%) */}
      <aside className="w-[360px] min-w-[360px] h-full bg-[#1e1e2e] border-r border-[#2e303a] flex flex-col p-6 shadow-2xl z-20 overflow-y-auto">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-[#f3f4f6] flex items-center gap-2">
            📍 TSPTW Optimizer
          </h1>
          <p className="text-xs text-[#9ca3af] mt-1">Optimizarea rutei curierului cu ferestre de timp</p>
        </div>

        {/* Selector Algoritm */}
        <div className="mb-4">
          <label className="text-xs font-bold uppercase text-[#c084fc] tracking-wider block mb-2">
            Algoritm de Optimizare
          </label>
          <select
            className="w-full bg-[#1f2028] text-[#f3f4f6] border border-[#2e303a] rounded-lg p-3 text-sm focus:outline-none focus:border-[#c084fc] cursor-pointer"
            value={selectedAlgo}
            onChange={(e) => setSelectedAlgo(e.target.value)}
          >
            <option value="ACO">Ant Colony Optimization (ACO)</option>
            <option value="GA">Algoritm Genetic (GA)</option>
            <option value="SA">Simulated Annealing (SA)</option>
            <option value="TSP2">TSP 2-Aproximativ (MST)</option>
            <option value="Christofides">Christofides (1.5-Aproximativ)</option>
            <option value="Clarke">Clarke-Wright Savings</option>
          </select>
        </div>

        {/* Butoane Acțiune */}
        <button
          onClick={handleRunAlgorithm}
          className="w-full bg-[#c084fc] hover:bg-[#a855f7] text-[#16171d] font-bold py-3 rounded-lg flex items-center justify-center gap-2 shadow-lg transition-all cursor-pointer mt-2"
        >
          ▶ Calculează Traseul Optim
        </button>

        <button className="w-full bg-[#1f2028] hover:bg-[#2e303a] text-[#f3f4f6] font-medium py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all cursor-pointer mt-3 border border-[#2e303a]">
          📊 Raport Comparativ
        </button>

        {/* Metrici / Rezultate */}
        <div className="mt-6 flex-1 flex flex-col gap-3">
          <span className="text-xs font-bold uppercase text-[#c084fc] tracking-wider">Metrici Traseu Generat</span>

          <div className="bg-[#1f2028] border border-[#2e303a] p-3 rounded-lg flex justify-between items-center">
            <span className="text-xs text-[#9ca3af]">Distanță Totală</span>
            <span className="font-bold text-[#f3f4f6]">{metrics.distance}</span>
          </div>
          <div className="bg-[#1f2028] border border-[#2e303a] p-3 rounded-lg flex justify-between items-center">
            <span className="text-xs text-[#9ca3af]">Timp Estimat</span>
            <span className="font-bold text-[#f3f4f6]">{metrics.time}</span>
          </div>
          <div className="bg-[#1f2028] border border-[#2e303a] p-3 rounded-lg flex justify-between items-center">
            <span className="text-xs text-[#9ca3af]">Timp Execuție</span>
            <span className="font-bold text-emerald-400">{metrics.execTime}</span>
          </div>
          <div className="bg-[#1f2028] border border-[#2e303a] p-3 rounded-lg flex justify-between items-center">
            <span className="text-xs text-[#9ca3af]">Ferestre Timp</span>
            <span className="font-bold text-emerald-400">{metrics.twCompliance}</span>
          </div>
        </div>

        <div className="text-[10px] text-center text-[#9ca3af] mt-auto pt-4">
          Licență Informatică • Universitatea Transilvania Brașov
        </div>
      </aside>

      {/* HARTA ÎN DREAPTA (Ocupă tot restul ecranului flexibil cu flex-1) */}
      <main className="flex-1 h-full relative bg-[#16171d] overflow-hidden">
        <style>{`
          .leaflet-tile {
            filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
          }
          .leaflet-container {
            background: #16171d !important;
            width: 100% !important;
            height: 100% !important;
            position: absolute !important;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
          }
        `}</style>

        <MapContainer
          center={[45.6579, 25.6050]}
          zoom={13}
          style={{ width: '100%', height: '100%' }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <Polyline positions={polylineCoords} color="#c084fc" weight={4} opacity={0.85} />

          {deliveryPoints.map((point) => (
            <Marker key={point.id} position={[point.lat, point.lon]}>
              <Popup>
                <div style={{ fontFamily: 'system-ui', minWidth: '140px', color: '#111' }}>
                  <b>{point.name}</b><br />
                  <span style={{ color: '#666', fontSize: '12px' }}>Interval: {point.tw}</span>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </main>

    </div>
  );
}