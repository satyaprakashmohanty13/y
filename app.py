import streamlit as st
import wave
import os
import subprocess

st.set_page_config(page_title="HiddenWave - Audio Steganography", layout="wide")

# --- Utility: Convert MP3 to WAV ---
def convert_mp3_to_wav(mp3_file_path, wav_file_path="converted.wav"):
    """
    Convert MP3 to WAV using FFmpeg subprocess.
    """
    subprocess.run([
        "ffmpeg", "-y", "-i", mp3_file_path, wav_file_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_file_path


# --- Embed Function ---
def embed_message(audio_file, message):
    try:
        if audio_file is None:
            return None, "❌ Error: Please upload an audio file."
        if not message:
            return None, "❌ Error: Please enter a secret message."

        # Save uploaded file temporarily
        uploaded_filename = audio_file.name
        temp_input_path = "temp_input"
        with open(temp_input_path, "wb") as f:
            f.write(audio_file.read())

        # Convert MP3 to WAV if needed
        if uploaded_filename.lower().endswith(".mp3"):
            input_path = convert_mp3_to_wav(temp_input_path, "converted.wav")
        else:
            input_path = temp_input_path

        # Open WAV and embed message
        waveaudio = wave.open(input_path, mode='rb')
        frame_bytes = bytearray(list(waveaudio.readframes(waveaudio.getnframes())))
        message = message + "###"
        message = message + int((len(frame_bytes) - (len(message) * 8 * 8)) / 8) * '#'
        bits = list(map(int, ''.join([bin(ord(i)).lstrip('0b').rjust(8, '0') for i in message])))

        for i, bit in enumerate(bits):
            frame_bytes[i] = (frame_bytes[i] & 254) | bit

        frame_modified = bytes(frame_bytes)
        output_path = "output.wav"
        with wave.open(output_path, 'wb') as fd:
            fd.setparams(waveaudio.getparams())
            fd.writeframes(frame_modified)

        waveaudio.close()

        with open(output_path, "rb") as f:
            audio_bytes = f.read()

        return audio_bytes, "✅ Message embedded successfully!"
    except Exception as e:
        return None, f"❌ Error: {str(e)}"


# --- Extract Function (WAV only) ---
def extract_message(audio_file):
    try:
        if audio_file is None:
            return "❌ Error: Please upload a WAV audio file."
        if not audio_file.name.lower().endswith(".wav"):
            return "⚠️ Only WAV files are supported for extraction."

        input_path = "temp_extract.wav"
        with open(input_path, "wb") as f:
            f.write(audio_file.read())

        waveaudio = wave.open(input_path, mode='rb')
        frame_bytes = bytearray(list(waveaudio.readframes(waveaudio.getnframes())))
        extracted = [frame_bytes[i] & 1 for i in range(len(frame_bytes))]
        string = "".join(chr(int("".join(map(str, extracted[i:i+8])), 2)) for i in range(0, len(extracted), 8))
        msg = string.split("###")[0]
        return f"🔐 Your Secret Message: {msg}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


# --- UI ---
st.title("🎧 HiddenWave: Hide Messages in Audio")

tab1, tab2 = st.tabs(["Embed Message", "Extract Message"])

with tab1:
    st.subheader("🔊 Embed a Secret Message")
    uploaded_audio = st.file_uploader("Upload an Audio File (.wav or .mp3)", type=["wav", "mp3"])
    secret_msg = st.text_input("Enter your secret message:")
    if st.button("Embed Message"):
        output_audio, status = embed_message(uploaded_audio, secret_msg)
        st.text(status)
        if output_audio:
            st.audio(output_audio, format="audio/wav")
            st.download_button("⬇️ Download Embedded Audio", data=output_audio, file_name="hidden_message.wav")

with tab2:
    st.subheader("🕵️ Extract a Hidden Message (WAV only)")
    uploaded_audio_extract = st.file_uploader("Upload a WAV File (.wav only)", type=["wav"], key="extract_audio")
    if st.button("Extract Message"):
        extracted_text = extract_message(uploaded_audio_extract)
        st.text_area("Extracted Message:", extracted_text, height=100)
