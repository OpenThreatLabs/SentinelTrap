"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import createGlobe from "cobe";
import {
  Globe as GlobeIcon,
  RefreshCw,
} from "lucide-react";

interface AdversaryOrigin {
  id: string;
  name: string;
  country: string;
  city: string;
  ip: string;
  protocol: string;
  location: [number, number]; // [lat, lng]
}

// Fixed Decoy Core (SentinelTrap Central Node in India)
const DECOY_TARGET: { name: string; country: string; location: [number, number] } = {
  name: "SentinelTrap HoneyCore :8080",
  country: "India (SOC Decoy Mesh)",
  location: [23.2599, 77.4126],
};

// Country coordinate lookup table for IP geolocation enrichment
const COUNTRY_COORDS: Record<string, [number, number]> = {
  Russia: [55.7558, 37.6173],
  China: [39.9042, 116.4074],
  "United States": [38.9072, -77.0369],
  USA: [38.9072, -77.0369],
  Germany: [50.1109, 8.6821],
  Netherlands: [52.3676, 4.9041],
  Brazil: [-23.5505, -46.6333],
  Japan: [35.6762, 139.6503],
  India: [28.6139, 77.2090],
  "United Kingdom": [51.5074, -0.1278],
  UK: [51.5074, -0.1278],
  France: [48.8566, 2.3522],
  Canada: [45.4215, -75.6972],
  Australia: [-33.8688, 151.2093],
  Singapore: [1.3521, 103.8198],
  Ukraine: [50.4501, 30.5234],
  Vietnam: [21.0285, 105.8542],
  Iran: [35.6892, 51.3890],
  Turkey: [39.9334, 32.8597],
  SouthKorea: [37.5665, 126.9780],
  "South Korea": [37.5665, 126.9780],
  Indonesia: [-6.2088, 106.8456],
  Bulgaria: [42.6977, 23.3219],
  Dubai: [25.2048, 55.2708],
  UAE: [25.2048, 55.2708],
  "United Arab Emirates": [25.2048, 55.2708],
};

// Convert [lat, lng] to 3D Cartesian coordinates matching COBE's exact spherical model
function latLngToVector([lat, lng]: [number, number]): [number, number, number] {
  const r = (lat * Math.PI) / 180;
  const a = (lng * Math.PI) / 180 - Math.PI;
  const o = Math.cos(r);
  return [-o * Math.cos(a), Math.sin(r), o * Math.sin(a)];
}

// Spherical Linear Interpolation (slerp) between two unit 3D vectors along the true great-circle geodesic
function slerp(
  p1: [number, number, number],
  p2: [number, number, number],
  t: number
): [number, number, number] {
  let dot = p1[0] * p2[0] + p1[1] * p2[1] + p1[2] * p2[2];
  dot = Math.max(-1, Math.min(1, dot));
  const omega = Math.acos(dot);
  if (Math.abs(omega) < 1e-6) return p1;
  const sinOmega = Math.sin(omega);
  const a = Math.sin((1 - t) * omega) / sinOmega;
  const b = Math.sin(t * omega) / sinOmega;
  return [
    a * p1[0] + b * p2[0],
    a * p1[1] + b * p2[1],
    a * p1[2] + b * p2[2],
  ];
}

// 3D Cartesian coordinates along the great-circle arc with arched parabolic elevation
function getArc3DPoint(
  p1: [number, number],
  p2: [number, number],
  t: number,
  baseRadius: number,
  maxElevation: number = 0.22
): [number, number, number] {
  const v1 = latLngToVector(p1);
  const v2 = latLngToVector(p2);
  const unit = slerp(v1, v2, t);
  // Parabolic elevation curve peaking at mid-transit (t = 0.5)
  const elevation = Math.sin(t * Math.PI) * maxElevation;
  const r = baseRadius + elevation;
  return [unit[0] * r, unit[1] * r, unit[2] * r];
}

export default function CobeGlobe({ className = "" }: { className?: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cobeCanvasRef = useRef<HTMLCanvasElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);

  const pointerX = useRef<number | null>(null);
  const pointerY = useRef<number | null>(null);
  // Start with phi facing the Indian subcontinent
  const phiRef = useRef(3.36);
  const thetaRef = useRef(0.25);
  const targetPhiRef = useRef<number | null>(null);
  const isDragging = useRef(false);

  // Live honeypot adversary targets state — initialized to EMPTY array so NO lines show until captured!
  const [adversaryTargets, setAdversaryTargets] = useState<AdversaryOrigin[]>([]);
  const [selectedAdversary, setSelectedAdversary] = useState<AdversaryOrigin | null>(null);
  const [autoRotate, setAutoRotate] = useState(true);
  const [hasLoaded, setHasLoaded] = useState(false);

  // Persistent refs so the WebGL globe and 60fps canvas loop never reset on background updates
  const clockRef = useRef(0);
  const adversaryTargetsRef = useRef<AdversaryOrigin[]>([]);
  const selectedAdversaryRef = useRef<AdversaryOrigin | null>(null);
  const autoRotateRef = useRef(true);
  const globeInstanceRef = useRef<any>(null);

  useEffect(() => {
    adversaryTargetsRef.current = adversaryTargets;
  }, [adversaryTargets]);

  useEffect(() => {
    selectedAdversaryRef.current = selectedAdversary;
  }, [selectedAdversary]);

  useEffect(() => {
    autoRotateRef.current = autoRotate;
  }, [autoRotate]);

  // Fetch real captured honeypot sessions from SentinelTrap Backend
  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "";
    const wsUrl =
      process.env.NEXT_PUBLIC_SENTINELTRAP_WS_URL ||
      (typeof window !== "undefined"
        ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws`
        : "");

    let isMounted = true;
    let ws: WebSocket | null = null;

    const loadLiveHoneypotOrigins = async () => {
      try {
        const res = await fetch(`${apiBase}/api/sessions`, { cache: "no-store" });
        if (res.ok && isMounted) {
          const sessions = await res.json();
          if (Array.isArray(sessions)) {
            const capturedList: AdversaryOrigin[] = [];

            sessions.forEach((s: any) => {
              // Extract real or enriched lat/lng
              let lat = s.latitude;
              let lng = s.longitude;

              // Fallback to Country coordinate if lat/lng is 0 or null
              if ((!lat && !lng) || (lat === 0 && lng === 0)) {
                const matched = COUNTRY_COORDS[s.country];
                if (matched) {
                  lat = matched[0];
                  lng = matched[1];
                }
              }

              // Exclude loopback or local targets matching India decoy
              const isDecoy =
                lat &&
                lng &&
                Math.abs(lat - DECOY_TARGET.location[0]) < 1 &&
                Math.abs(lng - DECOY_TARGET.location[1]) < 1;

              if (lat && lng && !isDecoy) {
                capturedList.push({
                  id: s.id || `session-${s.ip_address}`,
                  name: `${s.country} Ingress`,
                  country: s.country && s.country !== "Unknown" ? s.country : "External Ingress",
                  city: s.city && s.city !== "Unknown" ? s.city : "Remote Host",
                  ip: s.ip_address || "Unknown",
                  protocol: s.protocol ? `${s.protocol}` : "SSH :22",
                  location: [lat, lng],
                });
              }
            });

            // Deduplicate by IP or Country to keep the globe telemetry clean and diverse
            const uniqueOrigins: AdversaryOrigin[] = [];
            const seen = new Set<string>();

            for (const item of capturedList) {
              const key = `${item.country}-${item.city}-${item.ip}`;
              if (!seen.has(key)) {
                seen.add(key);
                uniqueOrigins.push(item);
              }
              if (uniqueOrigins.length >= 8) break;
            }

            // Only update React state if items actually changed to avoid triggering unnecessary renders
            setAdversaryTargets((prev) => {
              const prevKeys = prev.map((p) => `${p.id}-${p.country}`).join("|");
              const newKeys = uniqueOrigins.map((p) => `${p.id}-${p.country}`).join("|");
              if (prevKeys === newKeys) {
                return prev; // keep exact same array reference
              }
              return uniqueOrigins;
            });

            setSelectedAdversary((prev) => {
              if (uniqueOrigins.length === 0) return null;
              const exists = uniqueOrigins.find((o) => o.id === prev?.id);
              return exists || uniqueOrigins[0];
            });

            // If globe instance is alive, update its markers dynamically without re-creating WebGL
            if (globeInstanceRef.current) {
              const currentSelected = selectedAdversaryRef.current;
              const updatedMarkers = [
                {
                  location: DECOY_TARGET.location,
                  size: 0.045,
                  color: [0.08, 0.95, 0.85] as [number, number, number],
                  id: "target-core",
                },
                ...uniqueOrigins.map((adv) => ({
                  location: adv.location,
                  size: adv.id === currentSelected?.id ? 0.035 : 0.025,
                  color: (adv.id === currentSelected?.id
                    ? [1.0, 0.28, 0.65]
                    : [0.95, 0.75, 0.2]) as [number, number, number],
                  id: adv.id,
                })),
              ];
              globeInstanceRef.current.update({ markers: updatedMarkers });
            }
          }
        }
      } catch {
        // If fetch fails, keep existing state without forcing fallbacks
      } finally {
        if (isMounted) setHasLoaded(true);
      }
    };

    const setupWs = () => {
      try {
        ws = new WebSocket(wsUrl);
        ws.onmessage = () => {
          if (isMounted) loadLiveHoneypotOrigins();
        };
        ws.onclose = () => {
          if (isMounted) setTimeout(setupWs, 3000);
        };
      } catch {
        // fallback to interval
      }
    };

    loadLiveHoneypotOrigins();
    setupWs();

    const interval = setInterval(loadLiveHoneypotOrigins, 3000);

    return () => {
      isMounted = false;
      clearInterval(interval);
      ws?.close();
    };
  }, []);

  // Smoothly rotate globe to face chosen threat origin
  const focusLocation = useCallback((adv: AdversaryOrigin) => {
    setSelectedAdversary(adv);
    selectedAdversaryRef.current = adv;
    const target = Math.PI * 1.5 - (adv.location[1] * Math.PI) / 180;
    const current = phiRef.current;
    const diff = (target - (current % (Math.PI * 2))) % (Math.PI * 2);
    targetPhiRef.current = current + (diff > Math.PI ? diff - Math.PI * 2 : diff < -Math.PI ? diff + Math.PI * 2 : diff);

    // Update marker highlighting immediately without restarting globe
    if (globeInstanceRef.current) {
      const updatedMarkers = [
        {
          location: DECOY_TARGET.location,
          size: 0.028,
          color: [0.08, 0.95, 0.85] as [number, number, number],
          id: "target-core",
        },
        ...adversaryTargetsRef.current.map((targetAdv) => ({
          location: targetAdv.location,
          size: targetAdv.id === adv.id ? 0.035 : 0.025,
          color: (targetAdv.id === adv.id
            ? [1.0, 0.28, 0.65]
            : [0.95, 0.75, 0.2]) as [number, number, number],
          id: targetAdv.id,
        })),
      ];
      globeInstanceRef.current.update({ markers: updatedMarkers });
    }
  }, []);

  // Initialize COBE globe and persistent animation loop ONCE
  useEffect(() => {
    let width = 0;
    const onResize = () => {
      if (cobeCanvasRef.current && overlayCanvasRef.current) {
        width = cobeCanvasRef.current.offsetWidth;
        const dpr = window.devicePixelRatio || 2;
        overlayCanvasRef.current.width = width * dpr;
        overlayCanvasRef.current.height = width * dpr;
      }
    };
    window.addEventListener("resize", onResize);
    onResize();

    if (!cobeCanvasRef.current || !overlayCanvasRef.current) return;

    // 1. COBE markers: India Decoy Target Core + captured adversary targets
    const currentTargets = adversaryTargetsRef.current;
    const currentSelected = selectedAdversaryRef.current;
    const baseMarkers = [
      {
        location: DECOY_TARGET.location,
        size: 0.028,
        color: [0.08, 0.95, 0.85] as [number, number, number],
        id: "target-core",
      },
      ...currentTargets.map((adv) => ({
        location: adv.location,
        size: adv.id === currentSelected?.id ? 0.035 : 0.025,
        color: (adv.id === currentSelected?.id
          ? [1.0, 0.28, 0.65]
          : [0.95, 0.75, 0.2]) as [number, number, number],
        id: adv.id,
      })),
    ];

    // 2. Initialize COBE for the 3D globe dot sphere
    const globe = createGlobe(cobeCanvasRef.current, {
      devicePixelRatio: 2,
      width: width * 2,
      height: width * 2,
      phi: 3.36,
      theta: 0.25,
      dark: 1,
      diffuse: 1.4,
      mapSamples: 20000,
      mapBrightness: 8.0,
      mapBaseBrightness: 0.04,
      baseColor: [0.14, 0.18, 0.28], // GitHub dark-navy landmass
      markerColor: [0.18, 0.72, 1.0], // GitHub electric blue
      glowColor: [0.12, 0.38, 0.95], // GitHub atmospheric halo
      markers: baseMarkers,
      arcs: [],
      arcColor: [0.18, 0.72, 1.0],
      arcWidth: 0.2,
      arcHeight: 0.25,
      markerElevation: 0.01,
      scale: 1,
      offset: [0, 0],
    });

    globeInstanceRef.current = globe;
    let animationFrameId: number;
    const overlayCtx = overlayCanvasRef.current.getContext("2d");

    const animate = () => {
      // 1. Camera orbit rotation (Smooth continuous rotation)
      if (targetPhiRef.current !== null) {
        const delta = targetPhiRef.current - phiRef.current;
        if (Math.abs(delta) > 0.002) {
          phiRef.current += delta * 0.08;
        } else {
          phiRef.current = targetPhiRef.current;
          targetPhiRef.current = null;
        }
      } else if (!isDragging.current && autoRotateRef.current) {
        // Continuous 360-degree auto-rotation
        phiRef.current += 0.0025;
      }

      globe.update({
        phi: phiRef.current,
        theta: thetaRef.current,
      });

      // 2. Dedicated smooth 60fps line movement animation on overlay canvas
      if (overlayCtx && overlayCanvasRef.current) {
        const dpr = window.devicePixelRatio || 2;
        const w = overlayCanvasRef.current.width;
        const h = overlayCanvasRef.current.height;
        overlayCtx.clearRect(0, 0, w, h);

        clockRef.current += 0.0035; // Balanced, energetic laser transit speed
        const currentClock = clockRef.current;

        // Exact COBE projection mapping
        const cosTheta = Math.cos(thetaRef.current);
        const sinTheta = Math.sin(thetaRef.current);
        const cosPhi = Math.cos(phiRef.current);
        const sinPhi = Math.sin(phiRef.current);

        const project3D = (pt3D: [number, number, number]) => {
          const c = cosPhi * pt3D[0] + sinPhi * pt3D[2];
          const s = sinPhi * sinTheta * pt3D[0] + cosTheta * pt3D[1] - cosPhi * sinTheta * pt3D[2];
          const depth = -sinPhi * cosTheta * pt3D[0] + sinTheta * pt3D[1] + cosPhi * cosTheta * pt3D[2];

          // Screen space conversion matching COBE's normalized device coords
          const normX = (c + 1) / 2;
          const normY = (-s + 1) / 2;

          // Arc is elevated into space above the 0.8 sphere, so depth >= -0.28 remains visible
          // to prevent premature clipping when curving over the horizon
          return {
            x: normX * w,
            y: normY * h,
            visible: depth >= -0.28 || c * c + s * s >= 0.52,
            depth,
          };
        };

        // Render laser lines ONLY for real captured adversary targets
        const activeTargets = adversaryTargetsRef.current;
        const activeSelected = selectedAdversaryRef.current;
        const now = Date.now();

        // Track laser arrivals for target impact flare effects
        let closestImpactAlpha = 0;

        activeTargets.forEach((adv, idx) => {
          const isSelected = adv.id === activeSelected?.id;
          const offset = idx * 0.1428;
          const tProgress = (currentClock + offset) % 1; // 0 to 1 continuous loop

          // Sample 64 points along the 3D great-circle arc for ultra-smooth trajectory
          const segments = 64;
          const points: { x: number; y: number; visible: boolean; depth: number }[] = [];

          for (let s = 0; s <= segments; s++) {
            const fraction = s / segments;
            const pt3D = getArc3DPoint(adv.location, DECOY_TARGET.location, fraction, 0.8, 0.23);
            points.push(project3D(pt3D));
          }

          // A. Multi-layer subtle trajectory guide (dotted + subtle neon under-glow)
          overlayCtx.beginPath();
          let started = false;
          for (let i = 0; i < points.length; i++) {
            const pt = points[i];
            if (pt.visible) {
              if (!started) {
                overlayCtx.moveTo(pt.x, pt.y);
                started = true;
              } else {
                overlayCtx.lineTo(pt.x, pt.y);
              }
            } else {
              started = false;
            }
          }
          // Ambient arc guide with subtle dashed aesthetic
          overlayCtx.save();
          overlayCtx.setLineDash([4 * dpr, 6 * dpr]);
          overlayCtx.strokeStyle = isSelected
            ? "rgba(244, 63, 94, 0.35)"
            : "rgba(56, 189, 248, 0.18)";
          overlayCtx.lineWidth = (isSelected ? 1.5 : 1.0) * dpr;
          overlayCtx.stroke();
          overlayCtx.restore();

          // B. High-tech Traveling Plasma Laser Stream with White-Hot Core
          const beamSpan = 0.28;
          // Clean continuous flight loop allowing smooth entry from origin and full absorption at destination
          const cycleT = tProgress; // 0 to 1
          const headT = Math.min(1.0, cycleT * (1 + beamSpan));
          const tailT = Math.max(0.0, cycleT * (1 + beamSpan) - beamSpan);

          // Impact flare triggers as head arrives (0.90 to 1.0) and sustains as tail finishes absorbing (0.0 to 0.15 of next cycle)
          if (headT >= 0.88) {
            const strikeProgress = (headT - 0.88) / 0.12; // 0 to 1
            closestImpactAlpha = Math.max(closestImpactAlpha, Math.sin(strikeProgress * Math.PI * 0.5));
          } else if (cycleT < 0.12) {
            // Sustained dissipation flare as energy disperses into the decoy core
            const dissipate = 1 - cycleT / 0.12;
            closestImpactAlpha = Math.max(closestImpactAlpha, dissipate * 0.75);
          }

          if (headT > tailT) {
            const laserSteps = 42;
            const laserPts: { x: number; y: number; visible: boolean; intensity: number; t: number }[] = [];

            for (let j = 0; j <= laserSteps; j++) {
              const subFrac = j / laserSteps;
              const currentT = tailT + (headT - tailT) * subFrac;

              const pt3D = getArc3DPoint(adv.location, DECOY_TARGET.location, currentT, 0.8, 0.23);
              const p = project3D(pt3D);
              laserPts.push({
                x: p.x,
                y: p.y,
                visible: p.visible,
                intensity: subFrac,
                t: currentT,
              });
            }

            // Layer 1: Wide Volumetric Atmospheric Plasma Glow (Soft bloom)
            for (let k = 1; k < laserPts.length; k++) {
              const p0 = laserPts[k - 1];
              const p1 = laserPts[k];

              if (p0.visible || p1.visible) {
                overlayCtx.beginPath();
                overlayCtx.moveTo(p0.x, p0.y);
                overlayCtx.lineTo(p1.x, p1.y);

                // Non-linear power curve for intense head bloom that smoothly tapers down to zero at the tail
                const glowAlpha = Math.pow(p1.intensity, 2.0) * (isSelected ? 0.85 : 0.65);
                const glowWidth = (1.5 + Math.pow(p1.intensity, 1.5) * 6.5) * dpr;

                overlayCtx.strokeStyle = isSelected
                  ? `rgba(244, 63, 94, ${glowAlpha * 0.45})`
                  : `rgba(6, 182, 212, ${glowAlpha * 0.45})`;
                overlayCtx.lineWidth = glowWidth;
                overlayCtx.lineCap = "round";
                overlayCtx.stroke();
              }
            }

            // Layer 2: Main Saturated Energy Beam (Gradient-interpolated body)
            for (let k = 1; k < laserPts.length; k++) {
              const p0 = laserPts[k - 1];
              const p1 = laserPts[k];

              if (p0.visible || p1.visible) {
                overlayCtx.beginPath();
                overlayCtx.moveTo(p0.x, p0.y);
                overlayCtx.lineTo(p1.x, p1.y);

                const alpha = Math.max(0.04, Math.pow(p1.intensity, 1.3)) * (isSelected ? 1.0 : 0.95);
                const strokeWidth = (0.8 + Math.pow(p1.intensity, 1.2) * 3.2) * dpr;

                overlayCtx.strokeStyle = isSelected
                  ? `rgba(251, 113, 133, ${alpha})`
                  : `rgba(34, 211, 238, ${alpha})`;
                overlayCtx.lineWidth = strokeWidth;
                overlayCtx.lineCap = "round";
                overlayCtx.stroke();
              }
            }

            // Layer 3: Razor-Sharp White-Hot Core Needle (Concentrated at the leading 50% of the beam)
            const coreStartIndex = Math.floor(laserPts.length * 0.50);
            for (let k = coreStartIndex; k < laserPts.length; k++) {
              const p0 = laserPts[k - 1];
              const p1 = laserPts[k];

              if (p0.visible || p1.visible) {
                overlayCtx.beginPath();
                overlayCtx.moveTo(p0.x, p0.y);
                overlayCtx.lineTo(p1.x, p1.y);

                const progressInCore = (k - coreStartIndex) / (laserPts.length - coreStartIndex);
                const coreAlpha = Math.pow(progressInCore, 1.4) * 0.98;
                const coreWidth = (0.7 + progressInCore * 1.0) * dpr;

                overlayCtx.strokeStyle = `rgba(255, 255, 255, ${coreAlpha})`;
                overlayCtx.lineWidth = coreWidth;
                overlayCtx.lineCap = "round";
                overlayCtx.stroke();
              }
            }

            // Layer 4: Floating Micro Energy Sparks trailing organically in the ionized wake
            const sparkInterval = 3;
            for (let s = sparkInterval; s < laserPts.length - 2; s += sparkInterval) {
              const sp = laserPts[s];
              if (sp.visible && sp.intensity > 0.2) {
                // Subtle organic vibration jitter
                const jitterX = Math.sin(now * 0.01 + s * 1.5) * 1.2 * dpr;
                const jitterY = Math.cos(now * 0.01 + s * 1.5) * 1.2 * dpr;
                const sparkSize = (0.6 + Math.pow(sp.intensity, 1.8) * 1.4) * dpr;
                const sparkAlpha = Math.pow(sp.intensity, 1.5) * 0.75;

                overlayCtx.beginPath();
                overlayCtx.arc(sp.x + jitterX, sp.y + jitterY, sparkSize, 0, Math.PI * 2);
                overlayCtx.fillStyle = isSelected
                  ? `rgba(254, 205, 211, ${sparkAlpha})`
                  : `rgba(207, 250, 254, ${sparkAlpha})`;
                overlayCtx.fill();
              }
            }

            // Layer 5: Constant-Size Laser Tip (Clean penetration with zero expansion)
            const leadPt = laserPts[laserPts.length - 1];
            if (leadPt && leadPt.visible) {
              // Outer plasma corona bloom (fixed size)
              overlayCtx.beginPath();
              overlayCtx.arc(leadPt.x, leadPt.y, (isSelected ? 4.0 : 3.0) * dpr, 0, Math.PI * 2);
              overlayCtx.fillStyle = isSelected ? "rgba(244, 63, 94, 0.45)" : "rgba(6, 182, 212, 0.45)";
              overlayCtx.fill();

              // Secondary energy halo (fixed size)
              overlayCtx.beginPath();
              overlayCtx.arc(leadPt.x, leadPt.y, (isSelected ? 2.6 : 2.0) * dpr, 0, Math.PI * 2);
              overlayCtx.fillStyle = isSelected ? "rgba(251, 113, 133, 0.85)" : "rgba(103, 232, 249, 0.85)";
              overlayCtx.fill();

              // Blinding white-hot core contact point (fixed size)
              overlayCtx.beginPath();
              overlayCtx.arc(leadPt.x, leadPt.y, (isSelected ? 1.6 : 1.3) * dpr, 0, Math.PI * 2);
              overlayCtx.fillStyle = "#ffffff";
              overlayCtx.shadowColor = isSelected ? "#f43f5e" : "#22d3ee";
              overlayCtx.shadowBlur = 10 * dpr;
              overlayCtx.fill();
              overlayCtx.shadowBlur = 0;
            }
          }

          // C. Threat Origin Marker Pin & Dual-Stage Expanding Radar Echoes
          const origin3D = latLngToVector(adv.location);
          const originRadius = 0.8 + 0.015;
          const originScreen = project3D([origin3D[0] * originRadius, origin3D[1] * originRadius, origin3D[2] * originRadius]);

          if (originScreen.visible) {
            // Echo Ring 1 (Primary radar wave)
            const cycle1 = ((now + idx * 450) % 2000) / 2000;
            const rad1 = (3 + cycle1 * 16) * dpr;
            const alpha1 = Math.max(0, 1 - Math.pow(cycle1, 0.8));

            overlayCtx.beginPath();
            overlayCtx.arc(originScreen.x, originScreen.y, rad1, 0, Math.PI * 2);
            overlayCtx.strokeStyle = isSelected
              ? `rgba(244, 63, 94, ${alpha1 * 0.85})`
              : `rgba(245, 158, 11, ${alpha1 * 0.75})`;
            overlayCtx.lineWidth = 1.3 * dpr;
            overlayCtx.stroke();

            // Echo Ring 2 (Secondary harmonic wave, offset by 35%)
            const cycle2 = ((now + idx * 450 + 700) % 2000) / 2000;
            const rad2 = (3 + cycle2 * 14) * dpr;
            const alpha2 = Math.max(0, 1 - Math.pow(cycle2, 0.8));

            overlayCtx.beginPath();
            overlayCtx.arc(originScreen.x, originScreen.y, rad2, 0, Math.PI * 2);
            overlayCtx.strokeStyle = isSelected
              ? `rgba(251, 113, 133, ${alpha2 * 0.45})`
              : `rgba(252, 211, 77, ${alpha2 * 0.4})`;
            overlayCtx.lineWidth = 1.0 * dpr;
            overlayCtx.stroke();

            // Core center node at origin
            overlayCtx.beginPath();
            overlayCtx.arc(originScreen.x, originScreen.y, (isSelected ? 3.5 : 2.5) * dpr, 0, Math.PI * 2);
            overlayCtx.fillStyle = isSelected ? "#f43f5e" : "#f59e0b";
            overlayCtx.shadowColor = isSelected ? "#f43f5e" : "#f59e0b";
            overlayCtx.shadowBlur = 10 * dpr;
            overlayCtx.fill();
            overlayCtx.shadowBlur = 0;

            // Render origin badge text with country name + threat indicator
            if (isSelected || activeTargets.length <= 6) {
              const labelText = adv.country;

              overlayCtx.font = `bold ${10 * dpr}px monospace`;
              const textWidth = overlayCtx.measureText(labelText).width;
              const padding = 7 * dpr;
              const boxHeight = 18 * dpr;
              const boxWidth = textWidth + padding * 2;
              const boxX = originScreen.x + 8 * dpr;
              const boxY = originScreen.y - boxHeight / 2;

              // Rounded glassmorphic telemetry badge
              overlayCtx.fillStyle = "rgba(6, 11, 24, 0.92)";
              overlayCtx.strokeStyle = isSelected ? "rgba(244, 63, 94, 0.75)" : "rgba(245, 158, 11, 0.55)";
              overlayCtx.lineWidth = 1 * dpr;

              overlayCtx.beginPath();
              overlayCtx.roundRect(boxX, boxY, boxWidth, boxHeight, 4 * dpr);
              overlayCtx.fill();
              overlayCtx.stroke();

              // Country Name with glowing fill
              overlayCtx.fillStyle = isSelected ? "#fecdd3" : "#fef08a";
              overlayCtx.fillText(labelText, boxX + padding, boxY + 12.5 * dpr);
            }
          }
        });

        // D. High-Tech Animated India Decoy Node (Micro Cyber Reticle + Phased Radar Beacon)
        const india3D = latLngToVector(DECOY_TARGET.location);
        const indiaRadius = 0.8 + 0.015;
        const indiaScreen = project3D([india3D[0] * indiaRadius, india3D[1] * indiaRadius, india3D[2] * indiaRadius]);

        if (indiaScreen.visible) {
          // 1. Dual-Phased Radar Sonar Waves (Refined, controlled radius between 3px and 12px)
          const pulse1 = (now % 2000) / 2000;
          const rad1 = (3 + pulse1 * 9) * dpr;
          const alpha1 = Math.max(0, 1 - Math.pow(pulse1, 0.7));

          overlayCtx.beginPath();
          overlayCtx.arc(indiaScreen.x, indiaScreen.y, rad1, 0, Math.PI * 2);
          overlayCtx.strokeStyle = `rgba(6, 182, 212, ${alpha1 * 0.8})`;
          overlayCtx.lineWidth = 1.1 * dpr;
          overlayCtx.stroke();

          const pulse2 = ((now + 1000) % 2000) / 2000;
          const rad2 = (3 + pulse2 * 9) * dpr;
          const alpha2 = Math.max(0, 1 - Math.pow(pulse2, 0.7));

          overlayCtx.beginPath();
          overlayCtx.arc(indiaScreen.x, indiaScreen.y, rad2, 0, Math.PI * 2);
          overlayCtx.strokeStyle = `rgba(99, 102, 241, ${alpha2 * 0.6})`;
          overlayCtx.lineWidth = 0.9 * dpr;
          overlayCtx.stroke();

          // 2. High-Tech Rotating Orbit Crosshairs (Micro Reticle)
          const angle = (now * 0.0015) % (Math.PI * 2);
          const reticleR = 6.5 * dpr;
          overlayCtx.save();
          overlayCtx.translate(indiaScreen.x, indiaScreen.y);
          overlayCtx.rotate(angle);

          for (let i = 0; i < 4; i++) {
            const a = i * (Math.PI / 2);
            overlayCtx.beginPath();
            overlayCtx.moveTo(Math.cos(a) * (reticleR - 1.5 * dpr), Math.sin(a) * (reticleR - 1.5 * dpr));
            overlayCtx.lineTo(Math.cos(a) * (reticleR + 1.5 * dpr), Math.sin(a) * (reticleR + 1.5 * dpr));
            overlayCtx.strokeStyle = "rgba(34, 211, 238, 0.75)";
            overlayCtx.lineWidth = 1.1 * dpr;
            overlayCtx.stroke();
          }
          overlayCtx.restore();

          // 3. Central Decoy Core Node (Crisp glowing cyan)
          overlayCtx.beginPath();
          overlayCtx.arc(indiaScreen.x, indiaScreen.y, 2.4 * dpr, 0, Math.PI * 2);
          overlayCtx.fillStyle = "#ffffff";
          overlayCtx.shadowColor = "#06b6d4";
          overlayCtx.shadowBlur = 8 * dpr;
          overlayCtx.fill();
          overlayCtx.shadowBlur = 0;

          // 4. Tactical India Telemetry Tag (Modern pill badge with coordinate telemetry)
          const labelText = "IND DECOY";
          overlayCtx.font = `bold ${8.5 * dpr}px monospace`;
          const textW = overlayCtx.measureText(labelText).width;
          const pad = 5 * dpr;
          const bH = 15 * dpr;
          const bW = textW + pad * 2;
          const bX = indiaScreen.x + 9 * dpr;
          const bY = indiaScreen.y - bH / 2;

          overlayCtx.fillStyle = "rgba(7, 14, 28, 0.90)";
          overlayCtx.strokeStyle = "rgba(6, 182, 212, 0.65)";
          overlayCtx.lineWidth = 1 * dpr;

          overlayCtx.beginPath();
          overlayCtx.roundRect(bX, bY, bW, bH, 3.5 * dpr);
          overlayCtx.fill();
          overlayCtx.stroke();

          overlayCtx.fillStyle = "#22d3ee";
          overlayCtx.fillText(labelText, bX + pad, bY + 10.5 * dpr);
        }
      }

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", onResize);
      globe.destroy();
      globeInstanceRef.current = null;
    };
  }, []);

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-[#070b14] p-5 shadow-2xl transition-all ${className}`}
    >
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-100 dark:border-zinc-800/80 pb-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-500/10 p-2.5 text-blue-400 border border-blue-500/30 shadow-[0_0_20px_rgba(59,130,246,0.3)]">
            <GlobeIcon className="h-5 w-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-zinc-900 dark:text-white tracking-tight">
                Global Threat Interception Globe
              </h3>
              <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-mono font-bold border transition-colors ${
                adversaryTargets.length > 0
                  ? "bg-rose-500/15 border-rose-500/40 text-rose-400"
                  : "bg-emerald-500/15 border-emerald-500/40 text-emerald-400"
              }`}>
                {adversaryTargets.length > 0 ? `${adversaryTargets.length} Intercepted Threats` : "Standby • Monitoring"}
              </span>
            </div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">
              Real-time geospatial threat telemetry and honeypot ingress trajectories.
            </p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setAutoRotate(!autoRotate)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold transition-all cursor-pointer ${
              autoRotate
                ? "bg-blue-500/10 border-blue-500/30 text-blue-400 hover:bg-blue-500/20"
                : "bg-zinc-100 dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400"
            }`}
          >
            <RefreshCw className={`h-3 w-3 ${autoRotate ? "animate-spin" : ""}`} />
            {autoRotate ? "Auto-Rotate ON" : "Auto-Rotate PAUSED"}
          </button>
        </div>
      </div>

      {/* Adversary Origin Selector Pills dynamically populated from real captured sessions */}
      {adversaryTargets.length > 0 ? (
        <div className="my-4 flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
          <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-rose-400 whitespace-nowrap pl-1 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-500 animate-ping" />
            Captured Origins:
          </span>
          {adversaryTargets.map((adv) => {
            const isSelected = selectedAdversary?.id === adv.id;
            return (
              <button
                key={adv.id}
                onClick={() => focusLocation(adv)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-semibold transition-all shrink-0 cursor-pointer border ${
                  isSelected
                    ? "bg-pink-500/15 border-pink-500/40 text-pink-400 shadow-[0_0_15px_rgba(236,72,153,0.35)] scale-105"
                    : "bg-zinc-100 dark:bg-zinc-900/80 border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-400 hover:border-zinc-400 dark:hover:border-zinc-700"
                }`}
              >
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    isSelected ? "bg-pink-400 animate-ping" : "bg-amber-400"
                  }`}
                />
                <span className="font-bold">{adv.country}</span>
              </button>
            );
          })}
        </div>
      ) : null}

      {/* Main Visualizer Stage */}
      <div className="relative flex items-center justify-center py-4">
        {/* Layered Globe Container */}
        <div
          ref={containerRef}
          className="relative w-full max-w-[600px] aspect-square flex items-center justify-center cursor-grab active:cursor-grabbing mx-auto touch-none select-none"
          onPointerDown={(e) => {
            pointerX.current = e.clientX;
            pointerY.current = e.clientY;
            isDragging.current = true;
            (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
          }}
          onPointerUp={(e) => {
            pointerX.current = null;
            pointerY.current = null;
            isDragging.current = false;
            try {
              (e.target as HTMLElement).releasePointerCapture?.(e.pointerId);
            } catch {}
          }}
          onPointerCancel={() => {
            pointerX.current = null;
            pointerY.current = null;
            isDragging.current = false;
          }}
          onPointerMove={(e) => {
            if (pointerX.current !== null && pointerY.current !== null && isDragging.current) {
              const deltaX = e.clientX - pointerX.current;
              const deltaY = e.clientY - pointerY.current;
              pointerX.current = e.clientX;
              pointerY.current = e.clientY;

              // Full 360-degree horizontal spin
              phiRef.current += deltaX * 0.007;

              // Gentle vertical tilt clamped naturally between -0.8 and +0.8 radians
              thetaRef.current = Math.max(-0.8, Math.min(0.8, thetaRef.current - deltaY * 0.004));
            }
          }}
        >
          {/* GitHub signature deep blue ambient halo glow behind globe */}
          <div className="absolute inset-4 rounded-full bg-[radial-gradient(circle,rgba(37,99,235,0.2)_0%,rgba(147,51,234,0.08)_50%,transparent_75%)] blur-2xl pointer-events-none" />

          {/* 1. COBE WebGL Globe Dot Sphere */}
          <canvas
            ref={cobeCanvasRef}
            className="w-full h-full object-contain pointer-events-auto absolute inset-0"
            style={{ width: "100%", height: "100%", maxWidth: "100%", aspectRatio: 1 }}
          />

          {/* 2. Dedicated 60fps Smooth Motion Laser Overlay Canvas */}
          <canvas
            ref={overlayCanvasRef}
            className="w-full h-full object-contain pointer-events-none absolute inset-0 z-10"
            style={{ width: "100%", height: "100%", maxWidth: "100%", aspectRatio: 1 }}
          />

          {/* Center drag hint */}
          <div className="absolute bottom-2 inset-x-0 text-center pointer-events-none z-20">
            <span className="text-[10px] font-mono tracking-wider uppercase text-zinc-400 dark:text-zinc-500 bg-zinc-100/80 dark:bg-[#0c1322]/80 px-3 py-1 rounded-full border border-zinc-200 dark:border-blue-900/30 backdrop-blur-sm">
              Drag to rotate 360°
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
