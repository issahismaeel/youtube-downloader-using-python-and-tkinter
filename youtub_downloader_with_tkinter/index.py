import os
import tkinter as tk
from tkinter import filedialog, messagebox
from pytube import YouTube
import threading
from moviepy.editor import VideoFileClip, AudioFileClip
import time

# Function to update the progress bar for video download
def update_progress_bar_video(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = (bytes_downloaded / total_size) * 100
    progress_var.set(f"Downloading Video: {yt.title} ({percentage:.2f}%)")
    root.update_idletasks()

# Function to update the progress bar for audio download
def update_progress_bar_audio(chunk, file_handle, bytes_remaining):
    total_size = audio_stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = (bytes_downloaded / total_size) * 100
    progress_var.set(f"Downloading Audio: {yt.title} ({percentage:.2f}%)")
    root.update_idletasks()

# Function to download a YouTube video with retry mechanism
def download_with_retries(stream, output_path, filename, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            stream.download(output_path, filename=filename)
            return True
        except Exception as e:
            attempt += 1
            time.sleep(2)  # wait before retrying
            if attempt == retries:
                raise e
    return False

# Function to download both video and audio from a YouTube video and merge them
def download_and_merge_video_audio(url, output_path):
    try:
        global yt, audio_stream
        yt = YouTube(url)

        # Register the progress callback for video
        yt.register_on_progress_callback(update_progress_bar_video)

        # Get the highest resolution stream available
        video_stream = yt.streams.get_highest_resolution()

        # Check if the resolution is below 720p
        if int(video_stream.resolution[:-1]) < 720:
            video_stream = yt.streams.filter(res="720p").first()
            if not video_stream:
                video_stream = yt.streams.get_highest_resolution()

        resolution = video_stream.resolution
        progress_var.set(f"Downloading Video: {yt.title} at {resolution}...")
        root.update_idletasks()

        # Create main folder named after the video title
        main_folder = os.path.join(output_path, f"{yt.title}")
        os.makedirs(main_folder, exist_ok=True)

        # Construct filename with indication of video type
        video_filename = f"{yt.title} [Video].{video_stream.mime_type.split('/')[1]}"
        video_filepath = os.path.join(main_folder, video_filename)

        # Download video with retry mechanism
        if download_with_retries(video_stream, main_folder, video_filename):
            progress_var.set("Video Download Progress: 100%")

            # Download audio
            audio_stream = yt.streams.filter(only_audio=True).first()
            if not audio_stream:
                raise ValueError("No audio stream available for this video.")

            progress_var.set(f"Downloading Audio: {yt.title}...")
            root.update_idletasks()

            # Construct filename with indication of audio type
            audio_filename = f"{yt.title} [Audio].{audio_stream.mime_type.split('/')[1]}"
            audio_filepath = os.path.join(main_folder, audio_filename)

            # Download audio with retry mechanism
            if download_with_retries(audio_stream, main_folder, audio_filename):
                progress_var.set("Audio Download Progress: 100%")

                # Merge audio and video
                progress_var.set(f"Merging Audio and Video: {yt.title}...")
                video_clip = VideoFileClip(video_filepath)
                audio_clip = AudioFileClip(audio_filepath)
                final_clip = video_clip.set_audio(audio_clip)
                final_output_path = os.path.join(main_folder, f"{yt.title}.mp4")
                final_clip.write_videofile(final_output_path, codec="libx264", audio_codec="aac")
                progress_var.set("Merge Progress: 100%")

                # Remove separate audio and video files
                os.remove(video_filepath)
                os.remove(audio_filepath)

                messagebox.showinfo("Success", f"Downloaded and Merged Video and Audio: {yt.title}")
        else:
            raise Exception("Failed to download video after multiple attempts.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download or merge video and audio: {e}")

# Function to start the download process for both video and audio
def start_download_video_and_audio():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Error", "Please enter a URL")
        return

    output_path = filedialog.askdirectory()
    if not output_path:
        messagebox.showerror("Error", "Please select a download directory")
        return

    threading.Thread(target=download_and_merge_video_audio, args=(url, output_path)).start()

# Create the main application window
root = tk.Tk()
root.title("Free YouTube Downloader")

# Create and place the URL entry widget
tk.Label(root, text="YouTube URL:").grid(row=0, column=0, padx=10, pady=10)
url_entry = tk.Entry(root, width=50)
url_entry.grid(row=0, column=1, padx=10, pady=10)

# Create and place the download button for both video and audio
download_button = tk.Button(root, text="Download and Merge Video and Audio", command=start_download_video_and_audio)
download_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

# Create and place the progress label
progress_var = tk.StringVar()
progress_var.set("Download Progress: 0%")
progress_label = tk.Label(root, textvariable=progress_var)
progress_label.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

# Run the application
root.mainloop()
