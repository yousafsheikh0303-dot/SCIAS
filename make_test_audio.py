from gtts import gTTS

text = "گندم کی فصل کو کب پانی دینا چاہیے"
gTTS(text=text, lang='ur').save('test_urdu.wav')
print("Saved test_urdu.wav with text:", text)