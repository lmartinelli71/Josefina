"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  useParams,
  useRouter,
} from "next/navigation";


type CaptionMessage = {
  type: string;
  status: "live" | "closed";
  text: string;
};


export default function ProducerSessionPage() {
  const params = useParams();
  const router = useRouter();

  const sessionId =
    params.sessionId as string;


  const [caption, setCaption] = useState(
    "Esperando subtítulos..."
  );

  const [status, setStatus] = useState(
    "Conectando..."
  );

  const [micActive, setMicActive] =
    useState(false);

  const [viewerUrl, setViewerUrl] =
    useState("");

  const [copied, setCopied] =
    useState(false);

  const [closing, setClosing] =
    useState(false);


  const mediaRecorderRef =
    useRef<MediaRecorder | null>(null);

  const audioSocketRef =
    useRef<WebSocket | null>(null);

  const mediaStreamRef =
    useRef<MediaStream | null>(null);


  // --------------------------------
  // LINK PARA VIEWERS
  // --------------------------------

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    setViewerUrl(
      `${window.location.origin}` +
      `/session/${sessionId}/viewer`
    );

  }, [sessionId]);


  // --------------------------------
  // COPIAR LINK
  // --------------------------------

  const copyViewerLink = async () => {
    try {
      await navigator.clipboard.writeText(
        viewerUrl
      );

      setCopied(true);

      setTimeout(() => {
        setCopied(false);
      }, 2000);

    } catch (error) {
      console.error(
        "No se pudo copiar el enlace:",
        error
      );
    }
  };


  // --------------------------------
  // LIMPIAR AUDIO LOCAL
  // --------------------------------

  const cleanupAudio = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !==
        "inactive"
    ) {
      mediaRecorderRef.current.stop();
    }

    mediaRecorderRef.current =
      null;


    if (
      mediaStreamRef.current
    ) {
      mediaStreamRef.current
        .getTracks()
        .forEach((track) => {
          track.stop();
        });

      mediaStreamRef.current =
        null;
    }


    if (
      audioSocketRef.current
    ) {
      audioSocketRef.current.close();

      audioSocketRef.current =
        null;
    }
  };


  // --------------------------------
  // INICIAR MICRÓFONO
  // --------------------------------

  const startMicrophone = async () => {
    try {
      const stream =
        await navigator.mediaDevices
          .getUserMedia({
            audio: true,
          });

      mediaStreamRef.current =
        stream;


      const audioSocket =
        new WebSocket(
          `ws://127.0.0.1:8000/ws/audio/${sessionId}`
        );

      audioSocket.binaryType =
        "arraybuffer";


      audioSocket.onopen = () => {
        setStatus(
          "Audio conectado al backend"
        );
      };


      audioSocket.onerror = (
        error
      ) => {
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


      audioSocketRef.current =
        audioSocket;


      const mediaRecorder =
        new MediaRecorder(
          stream,
          {
            mimeType:
              "audio/webm;codecs=opus",
          }
        );


      mediaRecorder.ondataavailable =
        async (event) => {

          if (
            event.data.size === 0
          ) {
            return;
          }

          const buffer =
            await event.data
              .arrayBuffer();

          if (
            audioSocket.readyState ===
            WebSocket.OPEN
          ) {
            audioSocket.send(
              buffer
            );
          }
        };


      mediaRecorder.start(500);

      mediaRecorderRef.current =
        mediaRecorder;

      setMicActive(true);

      setStatus(
        "Micrófono activo"
      );

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


  // --------------------------------
  // DETENER MICRÓFONO
  // --------------------------------

  const stopMicrophone = () => {
    cleanupAudio();

    setMicActive(false);

    setStatus(
      "Micrófono detenido"
    );
  };


  // --------------------------------
  // CERRAR SESIÓN
  // --------------------------------

  const closeSession = async () => {
    try {
      setClosing(true);

      cleanupAudio();

      setMicActive(false);

      const response = await fetch(
        `http://127.0.0.1:8000/sessions/${sessionId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error(
          "No se pudo cerrar la sesión"
        );
      }

      router.push(
        "/producer"
      );

    } catch (error) {
      console.error(
        "Error cerrando sesión:",
        error
      );

      setStatus(
        "No se pudo cerrar la sesión"
      );

      setClosing(false);
    }
  };


  // --------------------------------
  // VOLVER AL PANEL
  // --------------------------------

  const backToSessions = () => {
    window.open(
      "/producer",
      "_blank"
    );
  };


  // --------------------------------
  // WEBSOCKET DE SUBTÍTULOS
  // --------------------------------

  useEffect(() => {
    if (!sessionId) {
      return;
    }

    const ws =
      new WebSocket(
        `ws://127.0.0.1:8000/ws/captions/${sessionId}`
      );


    ws.onopen = () => {
      setStatus(
        "Conectado"
      );
    };


    ws.onmessage = (
      event
    ) => {
      const message:
        CaptionMessage =
        JSON.parse(
          event.data
        );

      if (
        message.type !==
        "caption"
      ) {
        return;
      }

      setCaption(
        message.text
      );

      if (
        message.status ===
        "live"
      ) {
        setStatus(
          "Traducción en vivo"
        );
      }

      if (
        message.status ===
        "closed"
      ) {
        setStatus(
          "Segmento completo"
        );
      }
    };


    ws.onclose = () => {
      console.log(
        "WebSocket de subtítulos cerrado"
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


  // --------------------------------
  // LIMPIAR MICRÓFONO SI SE CIERRA
  // LA PÁGINA
  // --------------------------------

  useEffect(() => {
    return () => {
      cleanupAudio();
    };
  }, []);


  return (
    <main className="min-h-screen bg-black text-white flex items-center justify-center">

      <div className="w-full max-w-5xl px-8 text-center">

        <div className="mb-4 text-lg text-gray-400">
          Josefina · Traducción en vivo
        </div>


        <div className="mb-8 text-sm text-gray-500">
          Sesión: {sessionId}
        </div>


        <div className="mb-10 flex flex-wrap gap-3 justify-center">

          <button
            onClick={backToSessions}
            className="rounded border border-gray-600 px-4 py-2"
          >
            Volver a sesiones
          </button>


          <button
            onClick={closeSession}
            disabled={closing}
            className="rounded border border-red-500 px-4 py-2 text-red-400 disabled:opacity-50"
          >
            {closing
              ? "Cerrando..."
              : "Cerrar sesión"}
          </button>

        </div>


        <div className="mb-12">

          <div className="text-sm text-gray-400 mb-3">
            Enlace para los viewers
          </div>


          <div className="flex flex-col md:flex-row gap-3 justify-center items-center">

            <div className="rounded border border-gray-700 px-4 py-3 text-sm text-gray-300 break-all">
              {viewerUrl}
            </div>


            <button
              onClick={copyViewerLink}
              className="rounded border border-white px-4 py-3 text-white font-medium"
            >
              {copied
                ? "Copiado"
                : "Copiar enlace"}
            </button>

          </div>

        </div>


        <div className="min-h-48 flex items-center justify-center">

          <p className="text-4xl md:text-6xl font-semibold leading-tight">
            {caption}
          </p>

        </div>


        <div className="mt-10 flex gap-4 justify-center">

          <button
            onClick={startMicrophone}
            disabled={micActive || closing}
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