🎣 Phishing Website Detection

📌 Project Overview

This project focuses on exploratory data analysis (EDA) and data preprocessing for a phishing website detection task. The dataset consists of engineered website-level features extracted from HTML structure, metadata, and hosting information.

The notebook demonstrates how raw, noisy web data can be inspected, cleaned, and prepared for downstream machine learning models.

📊 Dataset Summary:

	•	📦 Total rows: 10,500
	•	🧮 Total features: 16
	•	🔢 Feature types: Numeric + Categorical
	•	🎯 Target variable: label
	•	0 -> Phishing
	•	1 -> Legitimate

🔍 Key Observations from EDA

Exploratory data analysis revealed several important insights:

	•	📉 Numeric features showed high skewness, requiring scaling
	•	⚠️ Invalid negative values detected
	•	Example: NoOfImage = -31
	•	🗑️ Unnamed: 0 identified as an index column and removed
	•	🏷️ Categorical features (Industry, HostingProvider) contained missing values
	•	🔗 Strong correlations identified in:
	•	NoOfSelfRedirect
	•	LargestLineLength
	•	DomainAgeMonths
	•	Robots (binary)

📦 Outlier Analysis:

	•	🚨 Severe outliers present in multiple numeric features
	•	📊 Boxplots were used to visualize distributions
	•	⚖️ Findings influenced:
	•	Scaling decisions
	•	Model selection (tree-based models preferred)

🏷️ Data Preprocessing Summary

🔢 Numeric Features:

	•	Total: 13 columns
	•	🩹 Missing values: Median imputation
	•	📐 Scaling: StandardScaler

🔠 Categorical Features:

	•	Industry
	•	HostingProvider
	•	🩹 Missing values: Most frequent value imputation

🗑️ Dropped Columns:

	•	Unnamed: 0
	•	Removed entirely before modeling

🎯 Target Variable:

	•	Label
	•	Used stratified train-test split

✅ Key Takeaways:

	•	📊 Real-world web datasets often contain skewed distributions, outliers, and data quality issues
	•	🌳 Thorough EDA is essential before applying any machine learning models
	•	🚨 Feature preprocessing decisions should be informed directly by data characteristics 
	•	⚖️ The notebook provides a strong foundation for integrating classical ML models
