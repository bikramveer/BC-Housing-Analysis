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

 You can then run the script from the terminal using:

 ```bash
  python project.py data_bc.csv amenities_distances.csv CensusProfile2021.csv
 ```
 or
 ```bash
  python3 project.py data_bc.csv amenities_distances.csv CensusProfile2021.csv
 ```
 depending on your installe python version

---

## Output Files

Once you have completed running the script, you will be able to see the following output files in your folder:
 - **data.csv** - Cleaned data with all included features
 - **distribution.svg** - Boxplot showing the spread of scores across cities
 - **distribution_sorted.svg** - Boxplot sorted by median score per city
 - **feature_significance.svg** - Bar chart of feature coefficients from our regression model
 - **feature_significance_minus_sqft.svg** - Same as above but without the square footage bar

You should also see 2 OLS Regression Results outputted to your terminal. The first will be for the feature significance including 'property-sqft' and the second for feature significance without 'property-sqft'. We exclude 'property-sqft' from the second to get a more detailed comparison of the other features.

---

## Annotated Notebook

Yoou can also view the main workflow and code explanation in the included juypter notebook:
 - **annotated_notebook.ipynb** - inline notes and insights included

---

## Notes

 - If you'd like to rerun amenity distance calculations, make sure your Overpass API acces is not rate-limited and that ```geo.py``` includes caching (```amenity_cache.json```) to avoid redundant requests.

  - ```amenities_distances.csv``` can be regenerated using the cached API responses for speed and efficiency.

---

## Contact

Please feel free to reach out to any of our team members ifyou have questions or issues!