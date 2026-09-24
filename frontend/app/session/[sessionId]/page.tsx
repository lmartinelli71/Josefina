"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";


type CaptionMessage = {
  type: string;
  status: "live" | "closed";
  text: string;
};


export default function SessionPage() {
  const params = useParams();

  const sessionId = params.sessionId as string;

  const [caption, setCaption] = useState(
    "Esperando subtítulos..."
  );

  const [status, setStatus] = useState(
    "Conectando..."
  );


  useEffect(() => {
    if (!sessionId) {
      return;
    }

    const ws = new WebSocket(
      `ws://127.0.0.1:8000/ws/captions/${sessionId}`
    );

    ws.onopen = () => {
      setStatus("Conectado");
    };

    ws.onmessage = (event) => {
      const message: CaptionMessage =
        JSON.parse(event.data);

      if (message.type !== "caption") {
        return;
      }

      setCaption(message.text);

      if (message.status === "live") {
        setStatus("Traducción en vivo");
      }

      if (message.status === "closed") {
        setStatus("Segmento completo");
      }
    };

    ws.onclose = () => {
      setStatus("Conexión cerrada");
    };

    ws.onerror = () => {
      setStatus("Error de conexión");
    };

    return () => {
      ws.close();
    };
  }, [sessionId]);


  return (
    <main className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="w-full max-w-5xl px-8 text-center">

        <div className="mb-10 text-lg text-gray-400">
          Josefina · Traducción en vivo
        </div>

        <div className="min-h-48 flex items-center justify-center">
          <p className="text-4xl md:text-6xl font-semibold leading-tight">
            {caption}
          </p>
        </div>

        <div className="mt-10 text-sm text-gray-500">
          {status}
        </div>

      </div>
    </main>
  );
}