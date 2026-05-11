import streamlit as st
import pandas as pd
import math
import joblib
import os

# 1. PAGE CONFIG MUST BE FIRST
st.set_page_config(page_title="Kidney Decline Prediction Tool", layout="wide")

# 2. LOAD MODEL
current_dir = os.getcwd()
MODEL_FILE = os.path.join(current_dir, "ckd_model.pkl")
try:
    model_sklearn = joblib.load(MODEL_FILE)
except:
    st.error("Model file not found. Make sure 'ckd_model.pkl' is in the same folder.")
    st.stop()

# 3. eGFR FUNCTION
def calculate_egfr(creatinine, age, sex, is_black):
    if sex == 1:  # Male
        k = 0.9
        a = -0.411
        f_female = 1
    else:  # Female
        k = 0.7
        a = -0.329
        f_female = 1.018
    scr_k = creatinine / k
    term1 = min(scr_k, 1) ** a
    term2 = max(scr_k, 1) ** (-1.209)
    age_factor = 0.993 ** age
    race_factor = 1.159 if is_black == 1 else 1
    egfr = 141 * term1 * term2 * age_factor * f_female * race_factor
    return round(egfr, 1)

# 4. APP LAYOUT
st.title("🩺 Enhanced Kidney Decline Prediction Tool")
st.write("Enter patient details to calculate eGFR and predict kidney decline risk.")

# Sidebar for patient input
st.sidebar.header("Patient Information")

age = st.sidebar.number_input("Age(years)", min_value=0, max_value=120, step=1)
sex = st.sidebar.selectbox("Sex", ["M", "F"])
race = st.sidebar.selectbox("Is patient Black?", ["Yes", "No"])
creatinine = st.sidebar.number_input("Creatinine (mg/dL)", min_value=0.0, step=0.01)
urine_protein = st.sidebar.number_input("Urine Protein(mg/dL)", min_value=0.0, step=0.01)

if st.sidebar.button("Predict Risk"):
    # Convert inputs
    sex_val = 1 if sex == "M" else 0
    race_val = 1 if race == "Yes" else 0

    # eGFR calculation
    egfr = calculate_egfr(creatinine, age, sex_val, race_val)

    # --- CRITICAL FIX: Match Excel Column Names Exactly ---
    patient_df = pd.DataFrame({
        'Age': [age],                     # Must match Excel header
        'Creatinine mg/dl': [creatinine], # Must match Excel header
        'Urine Protein': [urine_protein], # Must match Excel header
        'Sex': [sex_val]                  # Must match Excel header
    })

    # Model prediction
    probability = model_sklearn.predict_proba(patient_df)[:,1][0]
    prediction_text = "DECLINE LIKELY" if probability >= 0.3 else "NO SIGNIFICANT DECLINE"

    # Layout results in two columns
    col1, col2 = st.columns(2)

    # Column 1: eGFR
    with col1:
        st.subheader("💧 eGFR Results")
        st.metric("Calculated eGFR", f"{egfr} mL/min/1.73m²")

        if egfr >= 90:
            st.success("Stage 1: Normal or High")
        elif egfr >= 60:
            st.info("Stage 2: Mildly Decreased")
        elif egfr >= 30:
            st.warning("Stage 3: Moderately Decreased")
        else:
            st.error("Stage 4/5: Severe Decline")

    # Column 2: Model Prediction
    with col2:
        st.subheader("🩺 Model Prediction")
        if prediction_text == "DECLINE LIKELY":
            st.error(prediction_text)
        else:
            st.success(prediction_text)
        st.write(f"Risk Probability: {probability:.2%}")

    # Additional insights
    st.subheader("🔍 Insights")
    if egfr >= 60 and probability >= 0.5:
        st.info("eGFR is normal, but the model predicts risk. Monitor urine protein and lifestyle factors.")
    elif egfr < 60 and probability < 0.3:
        st.warning("Caution")
    elif egfr < 60 and probability >= 0.3:
        st.error("Both eGFR and model predict kidney decline. Immediate follow-up recommended.")
    else:
        st.success("No significant risk detected. Continue routine monitoring.")