# paper2audio

Convert research papers to audio files. Currently, it reads one paragraph at a time, while generating audio files in the cache dir for the entire file.

> [!IMPORTANT]
> The repo is hosted on [CodeBerg](https://codeberg.org/) — a true FOSS alternative to Github. The Github version is a mirror. Please contribute or open issues [here](https://codeberg.org/Chenghao2023/paper2audio) when possible. [Why giving up on Github?](https://sfconservancy.org/GiveUpGitHub/)

## Features
- [x] Layout analysis for noise removal (native PDF files only). Following elements are moved by default:
    - Footnote
    - Page-header
    - Page-footer
    - Table
    - Formula
    - Picture
- [x] Rule based noise reduction:
    - References
    - Citations
- [x] TTS with GCP (This requires that you have an active project and have enabled TTS feature, make sure you are aware of the cost of doing so)
- [x] Convert the paper to a beautiful yet minimal html file so you can use whatever TTS you might prefer

## Usage

```bash
python -m paper2audio to-audio "/Users/chenghao/Zotero/storage/QFKMKFMV/Chen et al. - 2024 - Orion-14B Open-source Multilingual Large Language Models.pdf"
python -m paper2audio to-html "/Users/chenghao/Zotero/storage/QFKMKFMV/Chen et al. - 2024 - Orion-14B Open-source Multilingual Large Language Models.pdf" --output "output.html"
```

## Examples

Feel free to checkout the html output in `examples`.

## Acknowledgement

Thanks to [pierreguillou](https://huggingface.co/pierreguillou) for the layout model.

## License

MIT