import time


class CaptionAssembler:
    """
    Administra el texto parcial que llega desde Gemini Live
    y decide cuándo conviene solicitar una nueva traducción.

    Los parciales actualizan continuamente el subtítulo.
    La traducción se limita en frecuencia para evitar una llamada
    a Gemini por cada palabra recibida.
    """

    def __init__(
        self,
        translation_interval: float = 1.0,
    ):
        self.translation_interval = translation_interval

        self.current_text = ""
        self.last_translated_text = ""
        self.last_translation_time = 0.0

    def update(
        self,
        event_type: str,
        text: str,
    ) -> dict:
        """
        Procesa una transcripción parcial o final.

        Devuelve información para decidir:
        - qué texto mostrar;
        - si debe traducirse;
        - si el segmento es definitivo.
        """

        self.current_text = text

        now = time.monotonic()

        is_final = event_type == "final"

        enough_time_passed = (
            now - self.last_translation_time
            >= self.translation_interval
        )

        text_changed = (
            text != self.last_translated_text
        )

        should_translate = (
            text_changed
            and (
                is_final
                or enough_time_passed
            )
        )

        if should_translate:
            self.last_translation_time = now
            self.last_translated_text = text

        return {
            "text": text,
            "is_final": is_final,
            "should_translate": should_translate,
        }