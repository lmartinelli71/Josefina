"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";


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
  const router = useRouter();

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
  // CARGAR AL ENTRAR
  // Y ACTUALIZAR PERIÓDICAMENTE
  // --------------------------------

  useEffect(() => {
    loadSessions();

    const interval = setInterval(
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
  // ENTRAR A SESIÓN
  // --------------------------------

  const openProducer = (
    sessionId: string
  ) => {
    router.push(
      `/session/${sessionId}/producer`
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
  // TEXTO DEL ESTADO
  // --------------------------------

  const getStatusText = (
    session: SessionInfo
  ) => {
    if (
      session.status === "CLOSED"
    ) {
      return "Cerrada";
    }

    if (
      session.producer_connected
    ) {
      return "Transmitiendo";
    }

    return "Sin transmisión";
  };


  return (
    <main className="min-h-screen bg-black text-white">

      <div className="w-full max-w-5xl mx-auto px-8 py-12">

        <div className="text-center mb-12">

          <h1 className="text-5xl font-bold mb-4">
            Josefina
          </h1>

          <p className="text-xl text-gray-400">
            Panel de producción
          </p>

        </div>


        <div className="text-center mb-12">

          <button
            onClick={createSession}
            disabled={creating}
            className="
              bg-white
              text-black
              px-8
              py-4
              rounded-lg
              text-lg
              font-semibold
              disabled:opacity-50
            "
          >
            {creating
              ? "Creando sesión..."
              : "Crear nueva sesión"}
          </button>

        </div>


        {error && (
          <div className="text-center mb-8 text-red-400">
            {error}
          </div>
        )}


        {loading && (
          <div className="text-center text-gray-500">
            Cargando sesiones...
          </div>
        )}


        {!loading &&
          sessions.length === 0 && (
            <div className="text-center text-gray-500">
              No hay sesiones creadas.
            </div>
          )}


        {!loading &&
          sessions.length > 0 && (

            <div>

              <h2 className="text-2xl font-semibold mb-6">
                Sesiones
              </h2>


              <div className="space-y-5">

                {sessions.map(
                  (session) => {

                    const closed =
                      session.status ===
                      "CLOSED";

                    return (
                      <div
                        key={
                          session.session_id
                        }
                        className="
                          border
                          border-gray-700
                          rounded-lg
                          p-6
                        "
                      >

                        <div className="
                          flex
                          flex-col
                          md:flex-row
                          md:items-center
                          md:justify-between
                          gap-5
                        ">

                          <div>

                            <div className="text-sm text-gray-500">
                              Sesión
                            </div>

                            <div className="text-xl font-semibold">
                              {
                                session.session_id
                              }
                            </div>

                            <div className="mt-2 text-sm text-gray-400">
                              Estado:{" "}
                              <span className="text-white">
                                {
                                  getStatusText(
                                    session
                                  )
                                }
                              </span>
                            </div>

                            <div className="mt-1 text-sm text-gray-500">
                              Viewers:{" "}
                              {
                                session.viewer_count
                              }
                            </div>

                          </div>


                          <div className="flex flex-wrap gap-3">

                            <button
                              onClick={() =>
                                openProducer(
                                  session.session_id
                                )
                              }
                              disabled={closed}
                              className="
                                bg-white
                                text-black
                                px-4
                                py-2
                                rounded
                                font-medium
                                disabled:opacity-40
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
                                border
                                border-white
                                px-4
                                py-2
                                rounded
                                font-medium
                                disabled:opacity-40
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
                                border
                                border-red-500
                                text-red-400
                                px-4
                                py-2
                                rounded
                                font-medium
                                disabled:opacity-40
                              "
                            >
                              {closed
                                ? "Sesión cerrada"
                                : "Cerrar sesión"}
                            </button>

                          </div>

                        </div>

                      </div>
                    );
                  }
                )}

              </div>

            </div>
          )}

      </div>

    </main>
  );
}