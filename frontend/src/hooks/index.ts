import { useState, useEffect, useRef, useCallback } from 'react';
import { wsService } from '../services/websocket';
import type { WSMessage, WSMessageType } from '../types';

export function useWebSocket(types: (WSMessageType | 'ALL')[]) {
  const [lastMessage, setLastMessage] = useState<WSMessage | null>(null);
  const [connected, setConnected] = useState(wsService.connected);

  useEffect(() => {
    wsService.connect();
    const unsubs: (() => void)[] = [];

    const connUnsub = wsService.on('CONNECTED', () => setConnected(true));
    unsubs.push(connUnsub);

    types.forEach(t => {
      unsubs.push(wsService.on(t, (msg) => setLastMessage(msg)));
    });

    // poll connection status
    const timer = setInterval(() => setConnected(wsService.connected), 1500);

    return () => {
      unsubs.forEach(u => u());
      clearInterval(timer);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return { lastMessage, connected };
}

export function useInterval(cb: () => void, ms: number) {
  const saved = useRef(cb);
  useEffect(() => { saved.current = cb; }, [cb]);
  useEffect(() => {
    const id = setInterval(() => saved.current(), ms);
    return () => clearInterval(id);
  }, [ms]);
}

export function useAsyncData<T>(fetcher: () => Promise<T>, deps: unknown[] = [], interval?: number) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const d = await fetcher();
      setData(d);
      setError(null);
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => { load(); }, [load]);
  useInterval(load, interval ?? 30000);

  return { data, loading, error, reload: load };
}
