# Cybersecurity Risk Indicator Discovery

**Notebook:** [Phishing Risk Feature Profiling](phishing-risk-feature-profiling.ipynb)

This notebook contains exploratory analysis of website indicators and a binary phishing label. It is an **analytical research artifact**, not an operational threat-detection system.

## Input and reproducibility

- Supply your own SQLite database containing a table named `phishing_data`. The dataset is not committed to this repository.
- Start Jupyter in this folder, or set the environment variable `PHISHING_DB_PATH` to the absolute path of your SQLite database.
- If not set, `PHISHING_DB_PATH` defaults to `phishing_data.sqlite` in the current working directory.
- The notebook uses SQLite, pandas, NumPy, Matplotlib and Seaborn. A completed historical output in the notebook does not establish results for a newly supplied dataset.

**Labels:** `0` indicates phishing; `1` indicates a legitimate website.

For the reproducible machine-learning workflow, use the code under `../src/` and the [Solution Design & Implementation Guide](../docs/solution-design/solution-design-and-implementation-guide.md). See also the [Project Overview](../README.md).
