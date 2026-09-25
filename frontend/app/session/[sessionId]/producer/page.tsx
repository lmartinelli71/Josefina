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
  // LINK VIEWER
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

      setStatus(
        "No se pudo copiar el enlace"
      );
    }
  };


  // --------------------------------
  // LIMPIAR AUDIO
  // --------------------------------

  const cleanupAudio = () => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !==
        "inactive"
    ) {
      mediaRecorderRef.current.stop();
    }

    mediaRecorderRef.current = null;


    if (mediaStreamRef.current) {
      mediaStreamRef.current
        .getTracks()
        .forEach((track) => {
          track.stop();
        });

      mediaStreamRef.current = null;
    }


    if (audioSocketRef.current) {
      audioSocketRef.current.close();

      audioSocketRef.current = null;
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
  // VOLVER AL PANEL ORIGINAL
  // SIN DETENER LA TRANSMISIÓN
  // --------------------------------

  const backToSessions = () => {
    window.open(
      "http://localhost:3000/producer",
      "josefina-production-panel"
    );
  };

  // --------------------------------
  // WEBSOCKET SUBTÍTULOS
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
  // LIMPIAR SI REALMENTE
  // SE CIERRA ESTA PÁGINA
  // --------------------------------

  useEffect(() => {
    return () => {
      cleanupAudio();
    };
  }, []);


  return (
    <main className="min-h-screen bg-black text-white">

      <div className="
        mx-auto
        flex
        min-h-screen
        w-full
        max-w-7xl
        flex-col
        px-6
        py-7
        md:px-10
      ">


        {/* HEADER */}

        <header className="
          flex
          flex-col
          gap-5
          border-b
          border-gray-900
          pb-6
          md:flex-row
          md:items-center
          md:justify-between
        ">

          <div>

            <div className="
              mb-3
              flex
              items-center
              gap-3
            ">

              <span
                className={`
                  h-2.5
                  w-2.5
                  rounded-full
                  ${
                    micActive
                      ? "bg-emerald-400 animate-pulse"
                      : "bg-gray-600"
                  }
                `}
              />


              <span
                className={`
                  text-xs
                  font-semibold
                  uppercase
                  tracking-[0.25em]
                  ${
                    micActive
                      ? "text-emerald-300"
                      : "text-gray-500"
                  }
                `}
              >
                {micActive
                  ? "En vivo"
                  : "Preparada"}
              </span>

            </div>


            <h1 className="
              text-3xl
              font-bold
              tracking-tight
              md:text-4xl
            ">
              Josefina
            </h1>


            <div className="
              mt-2
              flex
              flex-wrap
              items-center
              gap-3
              text-sm
              text-gray-500
            ">

              <span>
                Sesión
              </span>

              <span className="
                rounded-md
                border
                border-gray-800
                bg-gray-950
                px-2
                py-1
                font-mono
                text-gray-300
              ">
                {sessionId}
              </span>

            </div>

          </div>


          <div className="
            flex
            flex-wrap
            gap-3
          ">

            <button
              onClick={backToSessions}
              className="
                rounded-lg
                border
                border-gray-700
                px-4
                py-2.5
                text-sm
                font-medium
                text-gray-300
                transition
                hover:border-gray-500
                hover:bg-gray-900
                hover:text-white
              "
            >
              ← Volver a sesiones
            </button>


            <button
              onClick={closeSession}
              disabled={closing}
              className="
                rounded-lg
                border
                border-red-500/60
                px-4
                py-2.5
                text-sm
                font-medium
                text-red-400
                transition
                hover:bg-red-500/10
                disabled:cursor-not-allowed
                disabled:opacity-40
              "
            >
              {closing
                ? "Cerrando..."
                : "Cerrar sesión"}
            </button>

          </div>

        </header>


        {/* LINK AUDIENCIA */}

        <section className="
          mt-7
          rounded-2xl
          border
          border-gray-800
          bg-gray-950/70
          p-5
        ">

          <div className="
            flex
            flex-col
            gap-5
            lg:flex-row
            lg:items-center
            lg:justify-between
          ">

            <div>

              <div className="
                text-sm
                font-semibold
              ">
                Enlace para la audiencia
              </div>


              <p className="
                mt-1
                text-xs
                text-gray-500
              ">
                Compartí este enlace con quienes
                quieran seguir los subtítulos.
              </p>

            </div>


            <div className="
              flex
              min-w-0
              flex-1
              flex-col
              gap-3
              lg:max-w-3xl
              lg:flex-row
            ">

              <div className="
                min-w-0
                flex-1
                rounded-lg
                border
                border-gray-800
                bg-black
                px-4
                py-3
                font-mono
                text-xs
                text-gray-400
                break-all
              ">
                {viewerUrl}
              </div>


              <button
                onClick={copyViewerLink}
                className="
                  whitespace-nowrap
                  rounded-lg
                  bg-white
                  px-5
                  py-3
                  text-sm
                  font-semibold
                  text-black
                  transition
                  hover:bg-gray-200
                "
              >
                {copied
                  ? "Copiado ✓"
                  : "Copiar enlace"}
              </button>

            </div>

          </div>

        </section>


        {/* SUBTÍTULOS */}

        <section className="
          flex
          flex-1
          items-center
          justify-center
          py-10
        ">

          <div className="
            w-full
            max-w-5xl
            text-center
          ">

            <div className="
              mb-6
              text-xs
              font-semibold
              uppercase
              tracking-[0.28em]
              text-gray-600
            ">
              Traducción en vivo
            </div>


            <div className="
              rounded-3xl
              border
              border-gray-900
              bg-gray-950/30
              px-6
              py-10
              md:px-10
              md:py-14
            ">

              <p className="
                mx-auto
                max-w-5xl
                text-3xl
                font-semibold
                leading-[1.15]
                tracking-tight
                md:text-5xl
                lg:text-6xl
              ">
                {caption}
              </p>

            </div>

          </div>

        </section>


        {/* CONTROLES */}

        <footer className="
          border-t
          border-gray-900
          pt-6
        ">

          <div className="
            flex
            flex-col
            gap-6
            md:flex-row
            md:items-center
            md:justify-between
          ">


            {/* ESTADO */}

            <div className="
              flex
              items-center
              gap-4
            ">

              <div
                className={`
                  flex
                  h-11
                  w-11
                  items-center
                  justify-center
                  rounded-full
                  border
                  ${
                    micActive
                      ? "border-emerald-500/40 bg-emerald-500/10"
                      : "border-gray-800 bg-gray-950"
                  }
                `}
              >

                <span
                  className={`
                    h-3
                    w-3
                    rounded-full
                    ${
                      micActive
                        ? "bg-emerald-400 animate-pulse"
                        : "bg-gray-600"
                    }
                  `}
                />

              </div>


              <div>

                <div className="
                  text-sm
                  font-semibold
                ">
                  {micActive
                    ? "Micrófono activo"
                    : "Micrófono detenido"}
                </div>


                <div className="
                  mt-1
                  text-xs
                  text-gray-500
                ">
                  {status}
                </div>

              </div>

            </div>


            {/* BOTONES */}

            <div className="
              flex
              flex-wrap
              gap-3
            ">

              <button
                onClick={startMicrophone}
                disabled={
                  micActive ||
                  closing
                }
                className="
                  rounded-lg
                  bg-white
                  px-6
                  py-3
                  text-sm
                  font-semibold
                  text-black
                  transition
                  hover:bg-gray-200
                  disabled:cursor-not-allowed
                  disabled:opacity-30
                "
              >
                Iniciar micrófono
              </button>


              <button
                onClick={stopMicrophone}
                disabled={!micActive}
                className="
                  rounded-lg
                  border
                  border-gray-600
                  px-6
                  py-3
                  text-sm
                  font-semibold
                  transition
                  hover:border-white
                  hover:bg-gray-900
                  disabled:cursor-not-allowed
                  disabled:opacity-30
                "
              >
                Detener micrófono
              </button>

            </div>

          </div>

        </footer>

      </div>

    </main>
  );
}