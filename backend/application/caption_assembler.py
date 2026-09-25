import time

from backend.domain.caption_segment import CaptionSegment


class CaptionAssembler:
    """
    Construye los segmentos de subtítulos traducidos
    que verá el usuario.

    Responsabilidades:
    - mantiene el segmento LIVE actual;
    - actualiza su texto;
    - decide cuándo cerrarlo;
    - devuelve CaptionSegment del dominio.
    """

    def __init__(
        self,
        session_id: str,
        language: str,
        min_chars: int = 50,
        max_chars: int = 140,
    ):
        self.session_id = session_id
        self.language = language

        self.min_chars = min_chars
        self.max_chars = max_chars

        self.current_segment: CaptionSegment | None = None

    def add_translation(
        self,
        fragment: str,
    ) -> dict:
        fragment = fragment.strip()

        if not fragment:
            return {
                "current": self.current_segment,
                "closed_segments": [],
            }

        # Si todavía no existe un segmento LIVE,
        # creamos uno.
        if self.current_segment is None:
            self.current_segment = CaptionSegment(
                session_id=self.session_id,
                start_time=time.monotonic(),
                texts={
                    self.language: "",
                },
            )

        current_text = self.current_segment.texts.get(
            self.language,
            "",
        )

        current_text = self._append_fragment(
            current_text,
            fragment,
        )

        self.current_segment.update_text(
            self.language,
            current_text,
        )

        closed_segments = []

        while True:
            current_text = (
                self.current_segment.texts[
                    self.language
                ]
            )

            cut_position = self._find_cut_position(
                current_text
            )

            if cut_position is None:
                break

            closed_text = current_text[
                :cut_position
            ].strip()

            remainder = current_text[
                cut_position:
            ].strip()

            if closed_text:
                # El segmento actual queda cerrado
                self.current_segment.update_text(
                    self.language,
                    closed_text,
                )

                self.current_segment.close(
                    time.monotonic()
                )

                closed_segments.append(
                    self.current_segment
                )

            # Si quedó texto pendiente,
            # comienza un nuevo segmento LIVE.
            if remainder:
                self.current_segment = CaptionSegment(
                    session_id=self.session_id,
                    start_time=time.monotonic(),
                    texts={
                        self.language: remainder,
                    },
                )

            else:
                self.current_segment = None
                break

        return {
            "current": self.current_segment,
            "closed_segments": closed_segments,
        }

    def current(
        self,
    ) -> CaptionSegment | None:
        return self.current_segment

    def reset(self) -> None:
        self.current_segment = None

    def _find_cut_position(
        self,
        text: str,
    ):
        """
        Busca un lugar natural para cerrar
        el subtítulo.
        """

        if len(text) < self.min_chars:
            return None

        # Primero buscamos final natural
        # de oración.
        for index in range(
            self.min_chars,
            len(text),
        ):
            if text[index] in ".!?":
                return index + 1

        # Todavía no es demasiado largo.
        if len(text) < self.max_chars:
            return None

        # Si superamos max_chars,
        # buscamos una pausa cercana al límite.
        search_area = text[
            self.min_chars:self.max_chars
        ]

        for separator in [
            ", ",
            "; ",
            ": ",
            " ",
        ]:
            position = search_area.rfind(
                separator
            )

            if position != -1:
                absolute_position = (
                    self.min_chars
                    + position
                    + len(separator)
                )

                return absolute_position

        # Último recurso.
        return self.max_chars

    def _append_fragment(
        self,
        current: str,
        fragment: str,
    ) -> str:
        if not current:
            return fragment

        if fragment[0] in ".,;:!?)]}":
            return current + fragment

        return current + " " + fragment