# 📤 How to Upload to Kaggle

Your complete, self-contained dataset package is ready at:
📁 **[`Cricket_Pitch_Weather_Benchmark_Kaggle.zip`](file:///c:/Users/SUBHASH%20B/Desktop/Cricket%20dataset/Cricket_Pitch_Weather_Benchmark_Kaggle.zip)** (~14.2 MB)

And the unzipped folder is also available at:
📁 **[`kaggle_upload/`](file:///c:/Users/SUBHASH%20B/Desktop/Cricket%20dataset/kaggle_upload/)**

---

## Option 1: Web Browser (Drag & Drop) — Fastest & Easiest

1. Open your browser and go to [kaggle.com/datasets/new](https://www.kaggle.com/datasets/new).
2. Enter the title: **`Cricket Pitch and Weather Performance Benchmark`**.
3. Drag and drop the zip file:
   `c:\Users\SUBHASH B\Desktop\Cricket dataset\Cricket_Pitch_Weather_Benchmark_Kaggle.zip`
4. Kaggle will automatically unpack the files:
   - `venues_master.csv`
   - `matches_enriched.csv`
   - `deliveries_enriched.parquet`
   - `deliveries_sample.csv`
   - `condition_benchmark_summary.csv`
   - Benchmark tables, charts, and `CODEBOOK.md`
5. In the **Description** box, copy-paste the text from **[`README.md`](file:///c:/Users/SUBHASH%20B/Desktop/Cricket%20dataset/README.md)**.
6. Click **Create**!

---

## Option 2: Using the Kaggle CLI (Command Line)

If you have the Kaggle API configured (`kaggle.json` in `~/.kaggle/`):

```bash
# Navigate to the folder or pass the path directly:
kaggle datasets create -p "c:\Users\SUBHASH B\Desktop\Cricket dataset\kaggle_upload"
```

The metadata file [`dataset-metadata.json`](file:///c:/Users/SUBHASH%20B/Desktop/Cricket%20dataset/kaggle_upload/dataset-metadata.json) is already included with all keywords, license (`CC-BY-4.0`), and title pre-filled.
