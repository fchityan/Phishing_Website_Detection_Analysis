🎣 Phishing Website Detection


📌 Project Overview

This project implements a complete machine learning pipeline for detecting phishing websites using a structured dataset stored in a SQLite database.

The pipeline covers the full lifecycle:

	•	Data ingestion
	•	Exploratory analysis
	•	Feature preprocessing
	•	Model training
	•	Model evaluation

The goal is to accurately distinguish phishing websites from legitimate websites, with particular emphasis on recall, as false negatives can have serious security implications.

📊 Dataset Summary:

	•	📦 Total rows: 10,500
	•	🧮 Total features: 16
	•	🔢 Feature types: Numeric + Categorical
	•	🎯 Target variable: label
	•	Phishing
	•	Legitimate

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

🏷️ Feature Processing Summary

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
   
🤖 Model Selection

Three classifiers were evaluated to compare performance across different modeling strategies:

📉 Logistic Regression:

	•	Fast and interpretable baseline
	•	Performs well on linear relationships
	•	Used for benchmarking

🌳 Random Forest:

	•	Handles non-linear patterns effectively
	•	Robust to outliers and noise
	•	Performs well with mixed feature types

🚀 Gradient Boosting:

	•	Sequential tree-based ensemble
	•	Strong predictive power
	•	Captures complex interactions between features

📈 Model Evaluation Metrics

Models were evaluated using:

	•	Precision
	•	Recall
	•	F1 Score

🏆 Model Evaluation Results:

	•	🌳 Random Forest
	•	Best recall
	•	Particularly valuable for phishing detection, where missing a phishing site is costly
	•	🚀 Gradient Boosting
	•	Best overall accuracy
	•	Strong balanced performance across metrics
	•	📉 Logistic Regression
	•	Performed significantly worse than tree-based models
	•	Useful primarily as a baseline

✅ Key Takeaways:

	•	📊 Proper preprocessing is critical for skewed and noisy web data
	•	🌳 Tree-based models outperform linear models for phishing detection
	•	🚨 Recall is a key metric in security-focused classification tasks
	•	⚖️ Scaling and outlier handling directly affect downstream performance
