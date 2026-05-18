import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import json
import pandas as pd
from PIL import Image

# Page Configuration
st.set_page_config(page_title="Survey Horizontal Extractor", page_icon="📊", layout="wide")

st.title("📊 Horizontal Survey Data Extractor")
st.write("Upload a survey photo to automatically append a single structured row matching your Google Sheet layout.")

# Initialize Connections
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("Setup Secrets Missing! Please configure GEMINI_API_KEY and Google Sheets credentials.")
    st.stop()

uploaded_file = st.file_uploader("Choose a survey form image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Survey Form", use_container_width=True)
    
    if st.button("🚀 Process & Append Row", type="primary"):
        with st.spinner("AI is parsing the layout into a horizontal row..."):
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Prompt tightly optimized to map values to your specific horizontal spreadsheet format
                prompt = (
                    "Analyze the survey image and extract data matching this specific horizontal order. "
                    "For multiple-choice questions, provide only the selected letter (A, B, or C). "
                    "For handwritten questions under Section E, extract the short text written.\n\n"
                    "Return your response strictly as a valid JSON object with the following keys. "
                    "Do not include markdown tags or ```json wrappers.\n\n"
                    "{\n"
                    "  \"NAME\": \"Full name from the form\",\n"
                    "  \"PAGE_1_A_BUDGET_1\": \"Selected letter (e.g., B)\",\n"
                    "  \"PAGE_1_A_BUDGET_2\": \"Selected letter\",\n"
                    "  \"PAGE_1_A_BUDGET_3\": \"Selected letter\",\n"
                    "  \"PAGE_1_B_SAVINGS_1\": \"Selected letter\",\n"
                    "  \"PAGE_1_B_SAVINGS_2\": \"Selected letter\",\n"
                    "  \"PAGE_1_B_SAVINGS_3\": \"Selected letter\",\n"
                    "  \"PAGE_1_C_UTANG_1\": \"Selected letter\",\n"
                    "  \"PAGE_1_C_UTANG_2\": \"Selected letter\",\n"
                    "  \"PAGE_1_C_UTANG_3\": \"Selected letter\",\n"
                    "  \"PAGE_1_D_SCAM_1\": \"Selected letter\",\n"
                    "  \"PAGE_1_D_SCAM_2\": \"Selected letter\",\n"
                    "  \"PAGE_1_D_SCAM_3\": \"Selected letter\",\n"
                    "  \"PAGE_2_A_BUDGET_1\": \"Selected letter\",\n"
                    "  \"PAGE_2_A_BUDGET_2\": \"Selected letter\",\n"
                    "  \"PAGE_2_B_SAVINGS_1\": \"Selected letter\",\n"
                    "  \"PAGE_2_B_SAVINGS_2\": \"Selected letter\",\n"
                    "  \"PAGE_2_B_SAVINGS_3\": \"Selected letter\",\n"
                    "  \"PAGE_2_C_UTANG_1\": \"Selected letter\",\n"
                    "  \"PAGE_2_C_UTANG_2\": \"Selected letter\",\n"
                    "  \"PAGE_2_C_UTANG_3\": \"Selected letter\",\n"
                    "  \"PAGE_2_D_SCAM_1\": \"Selected letter\",\n"
                    "  \"PAGE_2_D_SCAM_2\": \"Selected letter\",\n"
                    "  \"PAGE_2_D_SCAM_3\": \"Selected letter\",\n"
                    "  \"PAGE_2_E_1\": \"Extracted text answer\",\n"
                    "  \"PAGE_2_E_2\": \"Extracted text answer\",\n"
                    "  \"PAGE_2_E_3\": \"Extracted text answer\"\n"
                    "}"
                )
                
                response = model.generate_content([prompt, image])
                
                # JSON Cleaning
                raw_text = response.text.strip()
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("\n", 1)[1]
                if raw_text.endswith("```"):
                    raw_text = raw_text.rsplit("\n", 1)[0]
                raw_text = raw_text.strip("`").strip()
                
                data = json.loads(raw_text)
                
                # Convert the flat key-value pairs into an ordered array mapping to columns A through AA
                row_values = [
                    data.get("NAME", ""),
                    data.get("PAGE_1_A_BUDGET_1", ""),
                    data.get("PAGE_1_A_BUDGET_2", ""),
                    data.get("PAGE_1_A_BUDGET_3", ""),
                    data.get("PAGE_1_B_SAVINGS_1", ""),
                    data.get("PAGE_1_B_SAVINGS_2", ""),
                    data.get("PAGE_1_B_SAVINGS_3", ""),
                    data.get("PAGE_1_C_UTANG_1", ""),
                    data.get("PAGE_1_C_UTANG_2", ""),
                    data.get("PAGE_1_C_UTANG_3", ""),
                    data.get("PAGE_1_D_SCAM_1", ""),
                    data.get("PAGE_1_D_SCAM_2", ""),
                    data.get("PAGE_1_D_SCAM_3", ""),
                    data.get("PAGE_2_A_BUDGET_1", ""),
                    data.get("PAGE_2_A_BUDGET_2", ""),
                    data.get("PAGE_2_B_SAVINGS_1", ""),
                    data.get("PAGE_2_B_SAVINGS_2", ""),
                    data.get("PAGE_2_B_SAVINGS_3", ""),
                    data.get("PAGE_2_C_UTANG_1", ""),
                    data.get("PAGE_2_C_UTANG_2", ""),
                    data.get("PAGE_2_C_UTANG_3", ""),
                    data.get("PAGE_2_D_SCAM_1", ""),
                    data.get("PAGE_2_D_SCAM_2", ""),
                    data.get("PAGE_2_D_SCAM_3", ""),
                    data.get("PAGE_2_E_1", ""),
                    data.get("PAGE_2_E_2", ""),
                    data.get("PAGE_2_E_3", "")
                ]
                
                # Fetch existing sheet to safely append down to the next clear row
                existing_df = conn.read()
                
                # Build temporary DataFrame matching layout width
                new_row_df = pd.DataFrame([row_values], columns=existing_df.columns[:27])
                
                # Append and upload data
                updated_df = pd.concat([existing_df, new_row_df], ignore_index=True)
                conn.update(data=updated_df)
                
                st.success(f"🎉 Success! Row added for user: {data.get('NAME')}")
                st.subheader("Data Row Snapshot:")
                st.dataframe(new_row_df)
                
            except Exception as e:
                st.error(f"Error parsing or writing row: {e}")