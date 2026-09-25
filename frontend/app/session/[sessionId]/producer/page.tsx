"use client";

import { useEffect, useRef, useState } from "react";
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

  const [micActive, setMicActive] = useState(false);

  const mediaRecorderRef =
    useRef<MediaRecorder | null>(null);

  const audioSocketRef =
    useRef<WebSocket | null>(null);

  const mediaStreamRef =
    useRef<MediaStream | null>(null);

  const startMicrophone = async () => {
    try {
      // 1. Capturamos el micrófono
      const stream =
        await navigator.mediaDevices.getUserMedia({
          audio: true,
        });

      mediaStreamRef.current = stream;

      console.log("Micrófono conectado", stream);

      // 2. Abrimos un WebSocket exclusivo para AUDIO
      const audioSocket = new WebSocket(
        `ws://127.0.0.1:8000/ws/audio/${sessionId}`
      );

      audioSocket.binaryType = "arraybuffer";

      audioSocket.onopen = () => {
        console.log(
          "WebSocket de audio conectado"
        );

        setStatus(
          "Audio conectado al backend"
        );
      };

      audioSocket.onerror = (error) => {
        console.error(
          "Error en WebSocket de audio:",
          error
        );

        setStatus(
          "Error en conexión de audio"
        );
      };

      audioSocket.onclose = () => {
        console.log(
          "WebSocket de audio cerrado"
        );
      };

      audioSocketRef.current = audioSocket;

      // 3. MediaRecorder convierte el micrófono
      // en pequeños bloques WebM/Opus
      const mimeType =
        "audio/webm;codecs=opus";

      const mediaRecorder =
        new MediaRecorder(
          stream,
          {
            mimeType,
          }
        );

      console.log(
        "Formato de audio:",
        mediaRecorder.mimeType
      );

      mediaRecorder.ondataavailable =
        async (event) => {
          if (event.data.size === 0) {
            return;
          }

          console.log(
            "Chunk de audio:",
            event.data.size,
            "bytes"
          );

          // 4. Convertimos el Blob a bytes
          const buffer =
            await event.data.arrayBuffer();

          // 5. Mandamos los bytes al backend
          if (
            audioSocket.readyState ===
            WebSocket.OPEN
          ) {
            audioSocket.send(buffer);

            console.log(
              "Chunk enviado al backend:",
              buffer.byteLength,
              "bytes"
            );
          }
        };

      // Generamos un chunk cada 500 ms
      mediaRecorder.start(500);

      mediaRecorderRef.current =
        mediaRecorder;

      setMicActive(true);
    } catch (error) {
      console.error(
        "Error accediendo al micrófono:",
        error
      );

      setStatus(
        "No se pudo acceder al micrófono"
      );
    }
  };

  const stopMicrophone = () => {
    // Detenemos MediaRecorder
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !==
        "inactive"
    ) {
      mediaRecorderRef.current.stop();
    }

    // Cerramos las pistas físicas
    // del micrófono
    if (mediaStreamRef.current) {
      mediaStreamRef.current
        .getTracks()
        .forEach((track) => {
          track.stop();
        });

      mediaStreamRef.current = null;
    }

    // Cerramos WebSocket de audio
    if (audioSocketRef.current) {
      audioSocketRef.current.close();
      audioSocketRef.current = null;
    }

    setMicActive(false);
    setStatus("Micrófono detenido");
  };

  // --------------------------------
  // WEBSOCKET DE SUBTÍTULOS
  // --------------------------------

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
        setStatus(
          "Traducción en vivo"
        );
      }

      if (message.status === "closed") {
        setStatus(
          "Segmento completo"
        );
      }
    };

    ws.onclose = () => {
      setStatus(
        "Conexión de subtítulos cerrada"
      );
    };

    ws.onerror = () => {
      setStatus(
        "Error de conexión de subtítulos"
      );
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

        <div className="mt-10 flex gap-4 justify-center">

          <button
            onClick={startMicrophone}
            disabled={micActive}
            className="rounded bg-white px-5 py-3 text-black font-medium disabled:opacity-50"
          >
            Iniciar micrófono
          </button>

          <button
            onClick={stopMicrophone}
            disabled={!micActive}
            className="rounded border border-white px-5 py-3 text-white font-medium disabled:opacity-50"
          >
            Detener micrófono
          </button>

        </div>

        <div className="mt-10 text-sm text-gray-500">
          {micActive
            ? "Micrófono activo"
            : status}
        </div>

      </div>

    </main>
  );
}