# CMPT-353-Project

# Housing Desirability Analysis for Metro Vancouver

This project analyzes housing listings across Metro Vancouver to identify which cities are the most desirable to live in for the average BC resident. It combines real estate data, amenity proximity, and census income data to generate a weighted score for each property, then visualizes the results.

---

## Project Highlights

- **Web-scraped housing listings** from Realtor.ca
- **Amenity proximity analysis** using the Overpass API (OpenStreetMap)
- **Affordability scoring** based on average BC income
- **Custom scoring** with normalized features
- **Feature importance** analysis using OLS regression
- **Visualizations** of score distributions and feature significance

---

## Requirements

- Python 3.7+
- The following Python libraries (install via pip if needed):

```bash
pip install pandas numpy matplotlib seaborn requests statsmodels scikit-learn
```

---

## How to Run

 Before running, ensure the following CSV files are in your project folder:
  - **data_bc.csv**: Raw housing listings data
  - **amenities_distances.csv**: distances per property to amenities (precomputed)
  - **CensusProfile2021.csv**: Census income data

  ---

 You can then run the script from the terminal using:

 ```bash
  python project.py data_bc.csv amenities_distances.csv CensusProfile2021.csv
 ```
 or
 ```bash
  python3 project.py data_bc.csv amenities_distances.csv CensusProfile2021.csv
 ```
 depending on your installe python version