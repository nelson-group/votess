name: Draft PDF

on:
  push:
    paths:
      - joss/**
      - .github/workflows/draft-pdf.yml

jobs:
  paper:
    runs-on: ubuntu-latest
    name: Paper Draft
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Build draft PDF
        uses: openjournals/openjournals-draft-action@master
        with:
          journal: joss
          paper-path: joss/paper.md
      - name: Upload
        uses: actions/upload-artifact@v4
        with:
          name: paper
          # This is the output path where Pandoc will write the compiled
          # PDF. Note, this should be the same directory as the input
          # paper.md
          path: joss/paper.pdf