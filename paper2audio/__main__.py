import asyncio
import json
import os
from hashlib import md5

from rich.console import Console
from typer import Typer

from paper2audio.audio import play
from paper2audio.generate import generate
from paper2audio.html import text2html
from paper2audio.text import extract_layout

app = Typer()


async def generate_single_audio_async(
    part, voice_name="en-US-Wavenet-D", cache_dir=".cache"
):
    audio_file = f"{cache_dir}/{part['fingerprint']}.mp3"
    if os.path.exists(audio_file):
        return
    respone = generate(part, voice_name=voice_name)
    with open(audio_file, "wb") as f:
        f.write(respone.audio_content)


async def async_worker(tasks):
    while not tasks.empty():
        task = await tasks.get()
        await task


async def generate_audio_async(parts, voice_name="en-US-Wavenet-D", cache_dir=".cache"):
    tasks = asyncio.Queue()
    for part in parts:
        tasks.put_nowait(generate_single_audio_async(part, voice_name, cache_dir))
    workers = [asyncio.create_task(async_worker(tasks)) for _ in range(2)]
    await asyncio.gather(*workers)


async def play_audio_async(
    parts, console, cache_dir=".cache"
):
    for part in parts:
        fingerprint = part["fingerprint"]
        audio_file = f"{cache_dir}/{fingerprint}.mp3"
        while not os.path.exists(audio_file):
            await asyncio.sleep(1)

        text = part["text"]
        text_color = "red" if part["label"].startswith("Section") else "blue"
        console.print(f"[bold green]{part['label']}[/bold green]")
        console.print(f"[i {text_color}]{text}[/i {text_color}]")

        play(f"{cache_dir}/{fingerprint}.mp3")



@app.command()
def to_audio(
    path: str,
    voice_name: str = "en-US-Wavenet-D",
    cache_dir: str = ".cache",
):
    console = Console()
    parts = extract_layout(
        path,
        level="block",
        exclude=[
            "Footnote",
            "Page-header",
            "Page-footer",
            "Table",
            "Formula",
            "Picture",
        ],
        stop_at_section="References",
        merge_consecutive_section=True,
        remove_citations=True,
    )
    os.makedirs(cache_dir, exist_ok=True)

    for i, part in enumerate(parts):
        fingerprint = md5(
            json.dumps({"text": part["text"], "voice_name": voice_name}).encode()
        ).hexdigest()
        parts[i]["fingerprint"] = fingerprint

    asyncio.run(generate_audio_async(parts, voice_name, cache_dir))
    asyncio.run(play_audio_async(parts, console, cache_dir))

@app.command()
def to_html(
    path: str,
    output: str = "output.html",
):
    parts = extract_layout(
        path,
        level="block",
        exclude=[
            "Footnote",
            "Page-header",
            "Page-footer",
            "Table",
            "Formula",
            "Picture",
        ],
        stop_at_section="References",
        merge_consecutive_section=True,
        remove_citations=True,
    )

    with open(output, "w") as f:
        f.write(text2html(parts))

if __name__ == "__main__":
    app()
