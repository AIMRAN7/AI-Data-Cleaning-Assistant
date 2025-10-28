# 🧠 AI Data Cleaning Assistant

**A professional-grade Streamlit application for automated data cleaning and preparation.**

Perfect for data analysts, students, and businesses who need to quickly clean and prepare messy datasets.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📤 **Multi-Format Upload** | Support for CSV, Excel (.xlsx, .xls), and JSON files |
| 📊 **Data Overview** | Comprehensive statistics: rows, columns, data types, missing values |
| 🤖 **AI Cleaning Suggestions** | Intelligent recommendations for handling missing data, duplicates, and outliers |
| ⚡ **One-Click Fix** | Apply all suggested cleaning operations instantly |
| 📈 **Interactive Visualizations** | Missing value heatmaps, distribution plots, and column profiling |
| 💾 **Export Options** | Download cleaned data as CSV or Excel |
| 🎨 **Professional UI** | Clean, intuitive interface built with Streamlit |

---

## 🚀 Quick Start

### Installation

1. **Clone or download this project**
   ```bash
   cd "AI Data Cleaning Assistant"
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows PowerShell
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📖 How to Use

1. **Upload Your Dataset**
   - Click "Browse files" or drag-and-drop
   - Supported formats: `.csv`, `.xlsx`, `.xls`, `.json`

2. **Review Data Overview**
   - See dataset shape, column types, and missing value counts
   - View the first few rows of your data

3. **Check AI Suggestions**
   - Get intelligent recommendations for cleaning
   - See which columns need attention

4. **Apply Cleaning**
   - Click "✅ Apply All Suggestions" for automatic cleaning
   - Or manually clean specific columns

5. **Visualize Data Quality**
   - Missing values heatmap
   - Column distribution charts
   - Data type breakdown

6. **Export Clean Data**
   - Download as CSV or Excel
   - Use for analysis, machine learning, or reporting

---

## 🏗️ Project Structure

```
AI Data Cleaning Assistant/
│
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── utils/                      # Helper modules
│   ├── __init__.py
│   ├── data_analyzer.py       # Data analysis and profiling
│   └── data_cleaner.py        # Cleaning operations
│
├── sample_data/               # Example datasets
│   └── sample_sales.csv
│
└── .github/
    └── copilot-instructions.md
```

---

## 🧪 Example Datasets

Try the app with the included sample dataset in `sample_data/sample_sales.csv`, which contains:
- Missing values in multiple columns
- Duplicate rows
- Mixed data types
- Outliers

---

## 💻 Tech Stack

- **Streamlit** - Web framework for interactive UI
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **Matplotlib & Seaborn** - Data visualization
- **Plotly** - Interactive charts
- **OpenPyXL** - Excel file support

---

## 🎯 Use Cases

✅ **Students** - Clean datasets for academic projects and assignments  
✅ **Data Analysts** - Prepare data for reporting and dashboards  
✅ **Small Businesses** - Clean sales, inventory, or customer data  
✅ **Researchers** - Prepare experimental data for analysis  
✅ **ML Engineers** - Pre-process datasets before model training  

---

## 🚀 Advanced Features (Future Roadmap)

- [ ] GPT-powered natural language explanations
- [ ] Advanced outlier detection (IQR, Isolation Forest)
- [ ] Google Sheets integration
- [ ] Data type auto-correction
- [ ] Custom cleaning rules
- [ ] Batch processing for multiple files
- [ ] Data validation rules
- [ ] Export to database (SQL)

---

## 💰 Monetization Ideas

If you want to sell this app:

1. **Freemium SaaS** - Host on Streamlit Cloud, charge for premium features
2. **Desktop App** - Package as `.exe` with PyInstaller, sell on Gumroad
3. **Fiverr Service** - Offer custom data cleaning as a service
4. **Enterprise License** - White-label for businesses

---

## 📝 License

This project is for educational and commercial use.

---

## 👨‍💻 Developer

**Abdullah Imran**

Built with ❤️ using Python and Streamlit

---

## 🤝 Contributing

Feel free to fork, improve, and submit pull requests!

---

**⭐ If you find this useful, please star the repository!**
