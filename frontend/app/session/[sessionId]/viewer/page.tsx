"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  useParams,
} from "next/navigation";


type CaptionMessage = {
  type: string;
  status: "live" | "closed";
  text: string;
};


export default function ViewerPage() {
  const params = useParams();

  const sessionId =
    params.sessionId as string;


  const [caption, setCaption] =
    useState(
      "Esperando subtítulos..."
    );

  const [status, setStatus] =
    useState(
      "Conectando..."
    );


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
      setStatus(
        "Conexión cerrada"
      );
    };


    ws.onerror = () => {
      setStatus(
        "Error de conexión"
      );
    };


    return () => {
      ws.close();
    };

  }, [sessionId]);


  const isLive =
    status === "Traducción en vivo";

  const isConnected =
    status === "Conectado" ||
    status === "Traducción en vivo" ||
    status === "Segmento completo";


  return (
    <main className="
      min-h-screen
      bg-black
      text-white
    ">

      <div className="
        mx-auto
        flex
        min-h-screen
        w-full
        max-w-7xl
        flex-col
        px-6
        py-8
        md:px-10
      ">


        {/* HEADER */}

        <header className="
          flex
          items-center
          justify-between
          border-b
          border-gray-900
          pb-5
        ">

          <div>

            <h1 className="
              text-xl
              font-semibold
              tracking-tight
              text-gray-200
            ">
              Josefina
            </h1>

            <p className="
              mt-1
              text-xs
              uppercase
              tracking-[0.22em]
              text-gray-600
            ">
              Traducción en vivo
            </p>

          </div>


          <div className="
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
                  isLive
                    ? "bg-emerald-400 animate-pulse"
                    : isConnected
                    ? "bg-sky-400"
                    : "bg-gray-600"
                }
              `}
            />

            <span className="
              text-xs
              font-medium
              text-gray-400
            ">
              {status}
            </span>

          </div>

        </header>


        {/* ÁREA PRINCIPAL */}

        <section className="
          flex
          flex-1
          items-center
          justify-center
          py-10
        ">

          <div className="
            w-full
            max-w-6xl
          ">

            <div className="
              mb-6
              text-center
              text-xs
              font-semibold
              uppercase
              tracking-[0.3em]
              text-gray-700
            ">
              Subtítulos
            </div>


            <div className="
              rounded-3xl
              border
              border-gray-900
              bg-gray-950/40
              px-6
              py-12
              shadow-2xl
              md:px-12
              md:py-16
            ">

              <p className="
                mx-auto
                max-w-5xl
                text-center
                text-3xl
                font-semibold
                leading-[1.18]
                tracking-tight
                text-white
                md:text-5xl
                lg:text-6xl
              ">
                {caption}
              </p>

            </div>

          </div>

        </section>


        {/* FOOTER */}

        <footer className="
          border-t
          border-gray-900
          pt-5
        ">

          <div className="
            flex
            flex-col
            gap-2
            text-xs
            text-gray-600
            sm:flex-row
            sm:items-center
            sm:justify-between
          ">

            <span>
              Sesión {sessionId}
            </span>

            <span>
              Live captions powered by Josefina
            </span>

          </div>

        </footer>

      </div>

    </main>
  );
}