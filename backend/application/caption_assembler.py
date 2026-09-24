class CaptionAssembler:
    """
    Construye el subtítulo traducido que verá el usuario.

    - Actualiza el texto mientras Gemini va traduciendo.
    - Prefiere cerrar en puntos, ! o ?.
    - Si el texto crece demasiado, intenta cortar en una pausa natural.
    - Nunca acumula toda la conferencia en un único string.
    """

    def __init__(
        self,
        min_chars: int = 50,
        max_chars: int = 140,
    ):
        self.min_chars = min_chars
        self.max_chars = max_chars

        self.current_text = ""

    def add_translation(
        self,
        fragment: str,
    ) -> dict:

        fragment = fragment.strip()

        if not fragment:
            return {
                "current": self.current_text,
                "closed_segments": [],
            }

        self.current_text = self._append_fragment(
            self.current_text,
            fragment,
        )

        closed_segments = []

        while True:

            cut_position = self._find_cut_position(
                self.current_text
            )

            if cut_position is None:
                break

            closed_text = self.current_text[
                :cut_position
            ].strip()

            remainder = self.current_text[
                cut_position:
            ].strip()

            if closed_text:
                closed_segments.append(
                    closed_text
                )

            self.current_text = remainder

        return {
            "current": self.current_text,
            "closed_segments": closed_segments,
        }

    def current(self) -> str:
        return self.current_text

    def reset(self) -> None:
        self.current_text = ""

    def _find_cut_position(
        self,
        text: str,
    ):
        """
        Busca un lugar natural para cerrar el subtítulo.
        """

        if len(text) < self.min_chars:
            return None

        # Primero buscamos final natural de oración.
        for index in range(
            self.min_chars,
            len(text),
        ):
            if text[index] in ".!?":
                return index + 1

        # Todavía no es demasiado largo.
        if len(text) < self.max_chars:
            return None

        # Si superamos max_chars, buscamos una pausa
        # cercana al límite.
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