import streamlit as st
import pandas as pd
import numpy as np
import joblib
import sys
import os
from arch import arch_model
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

st.set_page_config(page_title="Volatility Risk Dashboard", layout="wide")
import streamlit as st

st.title("📈 Stock Volatility Prediction App")
st.markdown("""
### 📁 How to Use
Upload a `.csv` file containing historical stock data.

The app will:
- Compute : log_return = ln(Close / Close_previous_day)
- Predict the stock's **future volatility**
- Visualize the volatility trend to help you assess risk

---

### 📊 Example of Required CSV Format

| Date       | Open   | High   | Low    | Close  | Volume | 
|------------|--------|--------|--------|--------|--------|
| 2023-01-01 | 100.0  | 105.0  | 99.0   | 104.0  | 50000  |
| 2023-01-02 | 104.0  | 108.0  | 102.0  | 107.5  | 52000  | 
| ...        | ...    | ...    | ...    | ...    | ...    | 
""")

st.sidebar.header("Settings")
num_days = st.sidebar.slider("Select number of past days to use", min_value=0, max_value=2000, value=500, step=50)

st.sidebar.header("Upload Returns Data")
file = st.sidebar.file_uploader("Upload returns.csv", type=["csv"])

if file:
    data = pd.read_csv(file, index_col=0, parse_dates=True)
else:
    data = pd.read_csv("data/raw/AAPL.csv", index_col=0, parse_dates=True)

data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
data['log_return'] = np.log(data['Close'] / data['Close'].shift(1))
data = data.tail(num_days)
data.dropna(subset=['log_return'], inplace=True)

st.subheader("Raw Data Preview (last 10 rows)")
st.dataframe(data.tail(10))

log_return = data['log_return'].values

if len(data) < 30:
    st.error("❌ Not enough data to fit GARCH model. Please select more days.")
    st.stop()

if num_days < 90:
    st.warning("⚠️ Volatility predictions may be unreliable with less than 90 days of data.")

model = arch_model(log_return, vol='GARCH', p=1, q=1)
model_fit = model.fit(disp='off')

forecast = model_fit.forecast(horizon=10)
forecasted_variance = forecast.variance.iloc[-1]
forecasted_volatility = np.sqrt(forecasted_variance)

tomorrow_vol = forecasted_volatility.iloc[0]

historical_volatility = data['log_return'].rolling(window=20).std().dropna()
threshold = np.percentile(historical_volatility, 75)
risk_level = "High Risk" if tomorrow_vol > threshold else "Low Risk"

st.write("📊 Tomorrow's Predicted Volatility:", tomorrow_vol)
st.write("📉 75th Percentile of Historical Volatility:", threshold)
st.metric("Risk Level", risk_level)

fig1, ax = plt.subplots(figsize=(12, 6))
ax.plot(forecasted_volatility, color='green', label='Last 10 Days Volatility')
ax.set_title("10 days predictions from GARCH(1,1) Model")
ax.set_xlabel("Date")
ax.set_ylabel("Volatility")
ax.legend()
ax.grid(True)
ax.tick_params(axis='x', rotation=45)
fig1.tight_layout()
st.pyplot(fig1)

fig2, ax2 = plt.subplots(figsize=(12, 4))
ax2.plot(historical_volatility[-100:].values, label='Historical Volatility')
ax2.axhline(threshold, color='red', linestyle='--', label='75% Threshold')
ax2.axhline(tomorrow_vol, color='blue', linestyle=':', label="Tomorrow's Prediction")
ax2.legend()
ax2.set_title("Volatility Comparison")
st.pyplot(fig2)


st.markdown("---")
st.caption("Built with using Garch model")