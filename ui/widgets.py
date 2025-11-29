from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.clock import Clock


class ChatBubble(MDCard):
    """Dymek czatu dla usera lub asystenta."""
    text = StringProperty("")
    is_user = BooleanProperty(True)

    def __init__(self, **kwargs):
        # UWAGA: Kivy może wywoływać on_text / on_is_user bardzo wcześnie.
        # Dlatego najpierw super(), a potem tworzymy label i dopiero wtedy stosujemy styl.
        super().__init__(**kwargs)

        self.padding = dp(10)
        self.spacing = dp(5)
        self.size_hint_x = 0.8
        self.size_hint_y = None
        self.elevation = 0

        # label może być użyty w on_text i _apply_style, więc trzymamy go na self
        self.label = MDLabel(
            text=self.text,
            theme_text_color="Custom",
            size_hint_y=None,
            valign="top",
        )
        self.label.bind(texture_size=self._update_height)
        self.add_widget(self.label)

        # reaguj na zmianę szerokości (np. resize okna)
        self.bind(width=lambda *args: self._update_height(self.label, None))

        # po zbudowaniu widgetu dociągamy styl i wysokość
        self._apply_style()
        Clock.schedule_once(lambda dt: self._update_height(self.label, None), 0)

    def _apply_style(self) -> None:
        """Ustaw kolory i promienie w zależności od roli."""
        # Bezpiecznik: jeśli label jeszcze nie istnieje, wyjdź
        if not hasattr(self, "label") or self.label is None:
            return

        if self.is_user:
            self.pos_hint = {"right": 1}
            self.radius = [15, 15, 0, 15]
            self.md_bg_color = (0.2, 0.6, 1, 1)
            text_color = (1, 1, 1, 1)
        else:
            self.pos_hint = {"x": 0}
            self.radius = [15, 15, 15, 0]
            self.md_bg_color = (0.9, 0.9, 0.9, 1)
            text_color = (0.1, 0.1, 0.1, 1)

        self.label.text_color = text_color

    def on_is_user(self, instance, value):
        # gdyby kiedyś zmieniać rolę dynamicznie
        self._apply_style()

    def on_text(self, instance, value):
        # Kivy potrafi wywołać on_text zanim __init__ stworzy label
        if not hasattr(self, "label") or self.label is None:
            return
        self.label.text = value
        self._update_height(self.label, None)

    def _update_height(self, instance, _):
        if self.width <= 0:
            return
        # Szerokość tekstu = szerokość karty - padding
        instance.text_size = (self.width - dp(20), None)
        instance.texture_update()
        instance.height = instance.texture_size[1]
        self.height = instance.texture_size[1] + dp(20)

    def update_text(self, new_text: str) -> None:
        """Metoda pomocnicza do streamingu."""
        self.text = new_text
