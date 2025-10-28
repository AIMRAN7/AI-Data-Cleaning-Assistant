# 🚀 Quick Start Guide

## Running the AI Data Cleaning Assistant

### Option 1: Using PowerShell (Recommended)
```powershell
cd "d:\AI Data Cleaning Assistant"
streamlit run app.py
```

### Option 2: Using Python directly
```powershell
cd "d:\AI Data Cleaning Assistant"
python -m streamlit run app.py
```

The app will automatically open in your default browser at `http://localhost:8501`

---

## 📝 First Time Setup

If you haven't installed the dependencies yet:

```powershell
cd "d:\AI Data Cleaning Assistant"
pip install -r requirements.txt
```

Or install manually:
```powershell
pip install streamlit pandas numpy matplotlib seaborn openpyxl plotly
```

---

## 🧪 Testing with Sample Data

1. Run the app using one of the commands above
2. In the sidebar, click "Browse files"
3. Navigate to `sample_data/sample_sales.csv`
4. Upload the file
5. Explore the AI suggestions and cleaning features!

The sample dataset includes:
- ✅ Missing values in multiple columns (Age, Income, Rating, etc.)
- ✅ Duplicate rows
- ✅ Potential outliers in Income column
- ✅ Mixed data quality issues

---

## 📁 Project Structure

```
AI Data Cleaning Assistant/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                # Full documentation
├── QUICK_START.md           # This file
│
├── utils/                   # Helper modules
│   ├── __init__.py
│   ├── data_analyzer.py    # Data analysis logic
│   └── data_cleaner.py     # Cleaning operations
│
├── sample_data/            # Example datasets
│   └── sample_sales.csv
│
└── .github/
    └── copilot-instructions.md
```

---

## 🎯 Key Features to Try

1. **Upload Data** → Try CSV, Excel, or JSON files
2. **View AI Suggestions** → See smart cleaning recommendations
3. **Apply All Fixes** → One-click data cleaning
4. **Explore Visualizations** → Missing values heatmap, distributions
5. **Export Clean Data** → Download as CSV or Excel

---

## 💡 Tips

- Use the sample dataset to understand how the app works
- The app automatically detects missing values, duplicates, and outliers
- All cleaning operations are non-destructive (original data is preserved)
- Export your cleaned data in CSV or Excel format

---

## 🐛 Troubleshooting

**"Module not found" error?**
```powershell
pip install -r requirements.txt
```

**Port already in use?**
```powershell
streamlit run app.py --server.port 8502
```

**App not opening in browser?**
Manually navigate to: http://localhost:8501

---

## 📧 Support

For issues or questions, refer to the main README.md file.

---

**Built with ❤️ by Abdullah Imran**
