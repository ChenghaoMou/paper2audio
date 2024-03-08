# paper2audio

Convert research papers to audio files. Currently, it reads one paragraph at a time, while generating audio files in the cache dir for the entire file.

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
- [x] TTS with GCP (This requires that you have an active project and have enabled TTS feature)

## Usage

```bash
python -m paper2audio "/Users/chenghao/Zotero/storage/QFKMKFMV/Chen et al. - 2024 - Orion-14B Open-source Multilingual Large Language Models.pdf"
```

## Acknowledgement

Thanks to [pierreguillou](https://huggingface.co/pierreguillou) for the layout model.

## License

MIT