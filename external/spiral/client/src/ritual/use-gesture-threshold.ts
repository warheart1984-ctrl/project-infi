import { useEffect, useMemo, useRef, useState } from "react";

export interface ThresholdEvent {
  sigil: string;
  velocity: number;
  precision: number;
  breached: boolean;
}

interface GestureThresholdTuning {
  memorySeedCount?: number | null;
  presenceFreshness?: number | null;
}

interface GesturePoint {
  x: number;
  y: number;
  t: number;
}

const DEFAULT_THRESHOLD_EVENT: ThresholdEvent = {
  sigil: "mirror-walker",
  velocity: 0,
  precision: 0,
  breached: false,
};

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function classifySigil(points: GesturePoint[]): { sigil: string; precision: number } {
  if (points.length < 2) {
    return { sigil: "mirror-walker", precision: 0 };
  }

  const start = points[0];
  const end = points[points.length - 1];
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const horizontalBias = Math.abs(dx) / (Math.abs(dy) + 1);
  const verticalBias = Math.abs(dy) / (Math.abs(dx) + 1);
  const distance = Math.hypot(dx, dy);

  if (horizontalBias > 1.5 && distance > 28) {
    return { sigil: "mirror-walker", precision: clamp(horizontalBias / 4, 0.2, 1) };
  }
  if (verticalBias > 1.5 && distance > 28) {
    return { sigil: "hollow-root", precision: clamp(verticalBias / 4, 0.2, 1) };
  }

  return { sigil: "breath-weaver", precision: 0.6 };
}

function detectRhythmSigil(intervals: number[]): string | null {
  if (intervals.length < 3) return null;
  const avg = intervals.reduce((sum, value) => sum + value, 0) / intervals.length;
  if (avg < 150) return "breath-weaver";
  if (avg < 280) return "mirror-walker";
  return null;
}

function resolvePrecisionWeight(tuning: GestureThresholdTuning | undefined): number {
  const memorySeedCount = Math.max(0, Math.floor(tuning?.memorySeedCount || 0));
  const memoryDensity = clamp(memorySeedCount / 24, 0, 1);
  const presenceFreshness = clamp(
    typeof tuning?.presenceFreshness === "number" && Number.isFinite(tuning.presenceFreshness)
      ? tuning.presenceFreshness
      : 0.5,
    0,
    1,
  );
  return clamp(0.9 + memoryDensity * 0.2 + presenceFreshness * 0.15, 0.8, 1.25);
}

export function useGestureThreshold(activeSigil: string, tuning?: GestureThresholdTuning) {
  const [thresholdEvent, setThresholdEvent] = useState<ThresholdEvent>(DEFAULT_THRESHOLD_EVENT);
  const pointsRef = useRef<GesturePoint[]>([]);
  const drawingRef = useRef(false);
  const lastKeyAtRef = useRef<number | null>(null);
  const keyIntervalsRef = useRef<number[]>([]);
  const focusDwellStartRef = useRef<number | null>(null);
  const tuningRef = useRef<GestureThresholdTuning | undefined>(tuning);

  useEffect(() => {
    tuningRef.current = tuning;
  }, [tuning?.memorySeedCount, tuning?.presenceFreshness]);

  useEffect(() => {
    const onPointerDown = (event: PointerEvent) => {
      drawingRef.current = true;
      pointsRef.current = [{ x: event.clientX, y: event.clientY, t: Date.now() }];
    };

    const onPointerMove = (event: PointerEvent) => {
      if (!drawingRef.current) return;
      pointsRef.current.push({ x: event.clientX, y: event.clientY, t: Date.now() });
    };

    const onPointerUp = () => {
      if (!drawingRef.current) return;
      drawingRef.current = false;
      const points = pointsRef.current;
      if (points.length < 2) return;

      const first = points[0];
      const last = points[points.length - 1];
      const ms = Math.max(1, last.t - first.t);
      const distance = Math.hypot(last.x - first.x, last.y - first.y);
      const velocity = clamp(distance / ms, 0, 4);
      const classified = classifySigil(points);
      const precisionWeight = resolvePrecisionWeight(tuningRef.current);
      const tunedPrecision = clamp(classified.precision * precisionWeight, 0, 1);
      const breached = classified.sigil === activeSigil && tunedPrecision >= 0.45 && velocity >= 0.02;
      setThresholdEvent({
        sigil: classified.sigil,
        precision: tunedPrecision,
        velocity,
        breached,
      });
    };

    const onKeyDown = () => {
      const now = Date.now();
      if (lastKeyAtRef.current !== null) {
        const interval = now - lastKeyAtRef.current;
        keyIntervalsRef.current = [...keyIntervalsRef.current.slice(-4), interval];
        const sigil = detectRhythmSigil(keyIntervalsRef.current);
        if (sigil) {
          const precisionWeight = resolvePrecisionWeight(tuningRef.current);
          setThresholdEvent({
            sigil,
            velocity: clamp(1 / Math.max(1, interval), 0, 4),
            precision: clamp(0.55 * precisionWeight, 0, 1),
            breached: sigil === activeSigil,
          });
        }
      }
      lastKeyAtRef.current = now;
    };

    const onFocusIn = () => {
      focusDwellStartRef.current = Date.now();
    };

    const onFocusOut = () => {
      if (!focusDwellStartRef.current) return;
      const dwellMs = Date.now() - focusDwellStartRef.current;
      focusDwellStartRef.current = null;
      if (dwellMs < 1200) return;
      const precisionWeight = resolvePrecisionWeight(tuningRef.current);
      setThresholdEvent({
        sigil: activeSigil,
        velocity: 0.1,
        precision: clamp(clamp(dwellMs / 5000, 0.3, 1) * precisionWeight, 0, 1),
        breached: true,
      });
    };

    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("focusin", onFocusIn);
    window.addEventListener("focusout", onFocusOut);

    return () => {
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerup", onPointerUp);
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("focusin", onFocusIn);
      window.removeEventListener("focusout", onFocusOut);
    };
  }, [activeSigil]);

  const normalizedEvent = useMemo<ThresholdEvent>(() => {
    const sigil = thresholdEvent.sigil || activeSigil;
    return {
      ...thresholdEvent,
      sigil,
      breached: thresholdEvent.breached && sigil === activeSigil,
    };
  }, [activeSigil, thresholdEvent]);

  return {
    thresholdEvent: normalizedEvent,
  };
}
