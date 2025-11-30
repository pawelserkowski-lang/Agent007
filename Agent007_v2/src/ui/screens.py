from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp
from kivy.properties import StringProperty

class ChatBubble(MDCard):
    text = StringProperty()
    sender = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(10)
        self.size_hint_y = None
        self.height = dp(60) # Dynamiczne dostosowanie w prawdziwej appce wymagałoby texture_size
        self.radius = [15, 15, 15, 0] if self.sender == 'bot' else [15, 15, 0, 15]
        self.md_bg_color = (0.1, 0.1, 0.1, 1) if self.sender == 'bot' else (0.2, 0.4, 0.8, 1)
        
        layout = MDBoxLayout(orientation='vertical')
        
        # Sender Label
        sender_lbl = MDLabel(text=self.sender.upper(), theme_text_color="Secondary", font_style="Caption", size_hint_y=None, height=dp(20))
        
        # Message Label
        msg_lbl = MDLabel(text=self.text, theme_text_color="Custom", text_color=(1,1,1,1))
        
        layout.add_widget(sender_lbl)
        layout.add_widget(msg_lbl)
        self.add_widget(layout)
