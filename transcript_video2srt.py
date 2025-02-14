import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import openai
from datetime import timedelta

openai.api_key = ''
model = 'whisper-1'

last_audio_file = None  # 定义全局变量

def open_file():
    global last_audio_file
    video_file_path = filedialog.askopenfilename(
        title="Select a video file",
        filetypes=[("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.mpeg *.mpg *.3gp *.m4v")]
    )
    if video_file_path:
        last_audio_file = convert_video_to_audio(video_file_path)

def convert_video_to_audio(video_file_path):
    audio_file_path = os.path.splitext(video_file_path)[0] + ".mp3"
    try:
        command = ["ffmpeg", "-i", video_file_path, "-vn", "-acodec", "libmp3lame", audio_file_path]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            messagebox.showinfo("Success", f"Audio extracted: {audio_file_path}")
            transcribe_button.config(state=tk.NORMAL)  # 这里解锁按钮
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, "Step 1 completed: Audio extracted!\n")
            return audio_file_path
        else:
            messagebox.showerror("Error", f"FFmpeg error: {result.stderr}")
            return None
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
        return None

def transcribe_audio(audio_file_path):
    try:
        with open(audio_file_path, "rb") as audio_file:
            response = openai.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="verbose_json"
            )
        return dict(response)
    except Exception as e:
        messagebox.showerror("Error", f"Transcription error: {e}")
        return None

def convert_json_to_srt(json_data, srt_file_path):
    if "segments" not in json_data:
        messagebox.showerror("Error", "Invalid transcription data!")
        return

    with open(srt_file_path, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(json_data["segments"], start=1):
            start_time = format_timestamp(segment["start"])
            end_time = format_timestamp(segment["end"])
            text = segment["text"]

            srt_file.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")

    messagebox.showinfo("Success", f"Transcription saved to {srt_file_path}")

def format_timestamp(seconds):
    t = timedelta(seconds=seconds)
    return str(t).replace('.', ',')[:-3]

def transcribe_and_save_custom():
    """ 选择音频文件，自定义 SRT 文件名称和目录后进行转换 """
    if not last_audio_file:
        messagebox.showerror("Error", "Please convert a video to audio first.")
        return

    file_name = simpledialog.askstring("Input", "Enter a name for the SRT file (without extension):", parent=root)
    if not file_name:
        return

    save_directory = filedialog.askdirectory(title="Select Directory to Save SRT File")
    if not save_directory:
        return

    srt_file_path = os.path.join(save_directory, f"{file_name}.srt")

    transcription_data = transcribe_audio(last_audio_file)

    if transcription_data:
        convert_json_to_srt(transcription_data, srt_file_path)
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"Transcription completed! SRT saved to {srt_file_path}\n")

root = tk.Tk()
root.title("Video & Audio Processing Tool")
root.geometry("500x300")

open_button = tk.Button(root, text="Open File (Convert to Audio)", command=open_file)
open_button.pack(pady=10)

transcribe_button = tk.Button(root, text="Transcribe and Save", state=tk.DISABLED, command=transcribe_and_save_custom)
transcribe_button.pack(pady=10)

output_text = tk.Text(root, wrap="word", height=10)
output_text.pack(pady=10)

root.mainloop()
