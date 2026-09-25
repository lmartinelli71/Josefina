"use client";

import {
  useEffect,
  useState,
} from "react";


type SessionInfo = {
  session_id: string;
  name: string;
  status: "READY" | "LIVE" | "CLOSED";
  producer_connected: boolean;
  viewer_count: number;
  producer_url: string;
  viewer_url: string;
};


export default function ProducerHomePage() {
  const [sessions, setSessions] =
    useState<SessionInfo[]>([]);

  const [creating, setCreating] =
    useState(false);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  // --------------------------------
  // CARGAR SESIONES
  // --------------------------------

  const loadSessions = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8000/sessions"
      );

      if (!response.ok) {
        throw new Error(
          "No se pudieron cargar las sesiones"
        );
      }

      const data: SessionInfo[] =
        await response.json();

      setSessions(data);
      setError("");

    } catch (error) {
      console.error(
        "Error cargando sesiones:",
        error
      );

      setError(
        "No se pudieron cargar las sesiones."
      );

    } finally {
      setLoading(false);
    }
  };


  // --------------------------------
  // REFRESCO AUTOMÁTICO
  // --------------------------------

  useEffect(() => {
    loadSessions();

    const interval =
      setInterval(
        loadSessions,
        2000
      );

    return () => {
      clearInterval(interval);
    };
  }, []);


  // --------------------------------
  // CREAR SESIÓN
  // --------------------------------

  const createSession = async () => {
    try {
      setCreating(true);
      setError("");

      const response = await fetch(
        "http://127.0.0.1:8000/sessions",
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error(
          "No se pudo crear la sesión"
        );
      }

      await response.json();

      await loadSessions();

    } catch (error) {
      console.error(
        "Error creando sesión:",
        error
      );

      setError(
        "No se pudo crear la sesión."
      );

    } finally {
      setCreating(false);
    }
  };


  // --------------------------------
  // ABRIR PRODUCTOR
  // --------------------------------

  const openProducer = (
    sessionId: string
  ) => {
    window.open(
      `/session/${sessionId}/producer`,
      "_blank"
    );
  };


  // --------------------------------
  // ABRIR VIEWER
  // --------------------------------

  const openViewer = (
    sessionId: string
  ) => {
    window.open(
      `/session/${sessionId}/viewer`,
      "_blank"
    );
  };


  // --------------------------------
  // CERRAR SESIÓN
  // --------------------------------

  const closeSession = async (
    sessionId: string
  ) => {
    try {
      setError("");

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

      await loadSessions();

    } catch (error) {
      console.error(
        "Error cerrando sesión:",
        error
      );

      setError(
        "No se pudo cerrar la sesión."
      );
    }
  };


  // --------------------------------
  // ESTADO
  // --------------------------------

  const getStatus = (
    session: SessionInfo
  ) => {
    if (
      session.status === "CLOSED"
    ) {
      return {
        text: "Cerrada",
        badge:
          "border-red-500/30 bg-red-500/10 text-red-300",
        dot:
          "bg-red-400",
      };
    }

    if (
      session.producer_connected
    ) {
      return {
        text: "En vivo",
        badge:
          "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
        dot:
          "bg-emerald-400 animate-pulse",
      };
    }

    return {
      text: "Lista",
      badge:
        "border-sky-500/30 bg-sky-500/10 text-sky-300",
      dot:
        "bg-sky-400",
    };
  };


  // --------------------------------
  // MÉTRICAS
  // --------------------------------

  const liveSessions =
    sessions.filter(
      (session) =>
        session.producer_connected &&
        session.status !== "CLOSED"
    ).length;

  const closedSessions =
    sessions.filter(
      (session) =>
        session.status === "CLOSED"
    ).length;

  const totalViewers =
    sessions.reduce(
      (total, session) =>
        total + session.viewer_count,
      0
    );


  return (
    <main className="min-h-screen bg-black text-white">

      <div className="mx-auto w-full max-w-6xl px-6 py-10 md:px-10">


        {/* HEADER */}

        <header className="mb-10 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">

          <div>

            <div className="mb-2 text-sm font-medium uppercase tracking-[0.25em] text-sky-400">
              Live translation platform
            </div>

            <h1 className="text-4xl font-bold tracking-tight md:text-5xl">
              Josefina
            </h1>

            <p className="mt-3 max-w-xl text-gray-400">
              Centro de producción para sesiones
              de traducción y subtítulos en vivo.
            </p>

          </div>


          <button
            onClick={createSession}
            disabled={creating}
            className="
              rounded-xl
              bg-white
              px-6
              py-3
              font-semibold
              text-black
              shadow-lg
              transition
              hover:bg-gray-200
              disabled:cursor-not-allowed
              disabled:opacity-50
            "
          >
            {creating
              ? "Creando..."
              : "+ Crear nueva sesión"}
          </button>

        </header>


        {/* MÉTRICAS */}

        <section className="mb-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

          <MetricCard
            label="Sesiones"
            value={sessions.length}
          />

          <MetricCard
            label="En vivo"
            value={liveSessions}
          />

          <MetricCard
            label="Viewers"
            value={totalViewers}
          />

          <MetricCard
            label="Cerradas"
            value={closedSessions}
          />

        </section>


        {/* ERROR */}

        {error && (
          <div className="mb-6 rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-red-300">
            {error}
          </div>
        )}


        {/* SESIONES */}

        <section>

          <div className="mb-5 flex items-center justify-between">

            <div>
              <h2 className="text-2xl font-semibold">
                Sesiones
              </h2>

              <p className="mt-1 text-sm text-gray-500">
                Administración de transmisiones activas y finalizadas
              </p>
            </div>

          </div>


          {loading && (
            <div className="rounded-2xl border border-gray-800 bg-gray-950 p-10 text-center text-gray-500">
              Cargando sesiones...
            </div>
          )}


          {!loading &&
            sessions.length === 0 && (
              <div className="rounded-2xl border border-dashed border-gray-700 bg-gray-950/50 p-14 text-center">

                <div className="mb-3 text-lg font-medium">
                  Todavía no hay sesiones
                </div>

                <p className="text-sm text-gray-500">
                  Creá una sesión para comenzar una transmisión.
                </p>

              </div>
            )}


          {!loading &&
            sessions.length > 0 && (

              <div className="space-y-4">

                {sessions.map(
                  (session) => {

                    const closed =
                      session.status ===
                      "CLOSED";

                    const state =
                      getStatus(session);

                    return (
                      <article
                        key={
                          session.session_id
                        }
                        className={`
                          rounded-2xl
                          border
                          p-6
                          transition
                          ${
                            closed
                              ? "border-gray-800 bg-gray-950/50 opacity-65"
                              : "border-gray-800 bg-gray-950 hover:border-gray-700"
                          }
                        `}
                      >

                        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">


                          {/* INFO */}

                          <div className="min-w-0">

                            <div className="mb-3 flex flex-wrap items-center gap-3">

                              <h3 className="text-xl font-semibold tracking-wide">
                                {
                                  session.session_id
                                }
                              </h3>

                              <span
                                className={`
                                  inline-flex
                                  items-center
                                  gap-2
                                  rounded-full
                                  border
                                  px-3
                                  py-1
                                  text-xs
                                  font-semibold
                                  ${state.badge}
                                `}
                              >
                                <span
                                  className={`
                                    h-2
                                    w-2
                                    rounded-full
                                    ${state.dot}
                                  `}
                                />

                                {state.text}

                              </span>

                            </div>


                            <div className="flex flex-wrap gap-x-7 gap-y-2 text-sm text-gray-400">

                              <div>
                                <span className="text-gray-600">
                                  Viewers
                                </span>

                                <span className="ml-2 font-medium text-white">
                                  {
                                    session.viewer_count
                                  }
                                </span>
                              </div>


                              <div>
                                <span className="text-gray-600">
                                  Productor
                                </span>

                                <span className="ml-2 font-medium text-white">
                                  {
                                    session.producer_connected
                                      ? "Conectado"
                                      : "Desconectado"
                                  }
                                </span>
                              </div>

                            </div>

                          </div>


                          {/* ACCIONES */}

                          <div className="flex flex-wrap gap-3">

                            <button
                              onClick={() =>
                                openProducer(
                                  session.session_id
                                )
                              }
                              disabled={closed}
                              className="
                                rounded-lg
                                bg-white
                                px-4
                                py-2.5
                                text-sm
                                font-semibold
                                text-black
                                transition
                                hover:bg-gray-200
                                disabled:cursor-not-allowed
                                disabled:opacity-30
                              "
                            >
                              Entrar como productor
                            </button>


                            <button
                              onClick={() =>
                                openViewer(
                                  session.session_id
                                )
                              }
                              disabled={closed}
                              className="
                                rounded-lg
                                border
                                border-gray-600
                                px-4
                                py-2.5
                                text-sm
                                font-medium
                                text-gray-200
                                transition
                                hover:border-white
                                hover:text-white
                                disabled:cursor-not-allowed
                                disabled:opacity-30
                              "
                            >
                              Abrir viewer
                            </button>


                            <button
                              onClick={() =>
                                closeSession(
                                  session.session_id
                                )
                              }
                              disabled={closed}
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
                                disabled:opacity-30
                              "
                            >
                              {closed
                                ? "Sesión cerrada"
                                : "Cerrar sesión"}
                            </button>

                          </div>

                        </div>

                      </article>
                    );
                  }
                )}

              </div>
            )}

        </section>


        {/* FOOTER */}

        <footer className="mt-12 border-t border-gray-900 pt-6 text-center text-xs text-gray-600">
          Josefina · Real-time translated captions
        </footer>

      </div>

    </main>
  );
}


// --------------------------------
// TARJETA MÉTRICA
// --------------------------------

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-950 p-5">

      <div className="text-sm text-gray-500">
        {label}
      </div>

      <div className="mt-2 text-3xl font-semibold">
        {value}
      </div>

    </div>
  );
}