# import streamlit as st
# from llm_consortium.core.runner import ConsortiumRunner
# from llm_consortium.config.models import ConsortiumConfig
# import asyncio
# import json
# import tempfile
# import pandas as pd
# import altair as alt
# from llm_consortium.utils.pricing import MODEL_PRICING, AVG_INPUT_TOKENS, AVG_OUTPUT_TOKENS, calculate_cost

# def main():
#     st.set_page_config(layout="wide", page_title="LLM Consortium")
    
#     st.markdown(
#         """
#         <style>
#         .block-container { padding-top: 1rem; padding-bottom: 0rem; }
#         div[data-testid="stHorizontalBlock"] { gap: 0.5rem; }
#         </style>
#         """, unsafe_allow_html=True
#     )
    
#     st.title("🔍 LLM Consortium - Multi-Model Evaluation")
    
#     runner = ConsortiumRunner()
#     if 'models' not in st.session_state:
#         st.session_state.models = []
    
#     col1, col2 = st.columns([2, 3])
    
#     with col1:
#         st.subheader("⚙️ Configuration")
#         model_selector = st.selectbox("Select Model", ["gpt-4o-mini", "gpt-3.5-turbo", "gemini-2", "o3-mini"])
#         instance_count = st.number_input("Instances", min_value=1, value=1, step=1)
        
#         if st.button("➕ Add Model"):
#             st.session_state.models = {(m, c) if m != model_selector else (m, instance_count) for m, c in st.session_state.models}
#             st.session_state.models.add((model_selector, instance_count))
#             st.rerun()
        
#         if st.session_state.models:
#             st.write("### Selected Models")
#             for idx, (model, count) in enumerate(st.session_state.models):
#                 cols = st.columns([4, 2, 1])
#                 with cols[0]:
#                     st.markdown(f"**{model}**")
#                 with cols[1]:
#                     st.markdown(f"Instances: {count}")
#                 with cols[2]:
#                     if st.button("❌", key=f"delete_{idx}"):
#                         st.session_state.models.remove((model, count))
#                         st.rerun()
#         else:
#             st.info("No models added yet")
        
#         arbiter = st.selectbox("Arbiter Model", ["gpt-4o-mini", "gemini-2", "gpt-3.5-turbo"], index=2)
#         confidence = st.slider("Confidence Threshold", 0.0, 1.0, 0.8)
#         max_iter = st.number_input("Max Iterations", min_value=1, value=3, step=1)
#         min_iter = st.number_input("Min Iterations", min_value=1, value=1, step=1)
    
#     with col2:
#         st.subheader("🚀 Execution")
#         prompt = st.text_area("Enter NLQ Prompt", height=150)
        
#         if st.session_state.models:
#             models_dict = {model: count for model, count in st.session_state.models}
#             total_cost, cost_df = calculate_cost([(m, c) for m, c in models_dict.items()] + [(arbiter, 1)], max_iter)
#             st.write(f"**💰 Estimated Cost:** ${total_cost:.4f}")
#             st.dataframe(cost_df, use_container_width=True)
#         else:
#             st.info("Add models to see cost estimation")
        
#         if st.button("▶️ Run Consortium", type="primary"):
#             if not st.session_state.models:
#                 st.error("Please add at least one model")
#                 return
            
#             config = ConsortiumConfig(
#                 models=models_dict,
#                 arbiter=arbiter,
#                 confidence_threshold=confidence,
#                 max_iterations=int(max_iter),
#                 min_iterations=int(min_iter)
#             )
#             result = asyncio.run(runner.run_consortium(config, prompt))
            
#             st.subheader("📊 Results")
#             st.write(f"**🔢 Actual Iterations:** {result.get('iterations', max_iter)}")
#             st.write(f"**📈 Final Cost:** ${total_cost:.4f}")
#             st.write(f"**📝 Synthesized Response:** {result.get('synthesis', {}).get('text', 'No synthesis result')}")
            
#             # responses = pd.DataFrame([
#             #     {
#             #         "Model": r.get("model", "Unknown"),
#             #         "Confidence": r.get("confidence", 0),
#             #         "Latency": f"{r.get('latency', 0):.2f}s",
#             #         "Response": r.get("response", "")[:100] + "..."
#             #     } for r in result.get("raw_responses", [])
#             # ])
#             responses = pd.DataFrame([
#                 {
#                     "Model": r.get("model", "Unknown"),
#                     "Confidence": r.get("confidence", 0),
#                     "Response": r.get("response", "")[:100] + "...",
#                     # Store latency as float, add formatted version for display
#                     "Latency": r.get("latency", 0),  # Keep as numerical value
#                     "Latency_str": f"{r.get('latency', 0):.2f}s"  # For display
#                 } for r in result.get("raw_responses", [])
#                 ])
#             st.dataframe(responses, use_container_width=True)
            
#             if not responses.empty:
#                 st.subheader("📌 Model Confidence Comparison")
#                 bar_chart = alt.Chart(responses).mark_bar().encode(
#                     x=alt.X('Model:N', title='Model'),
#                     y=alt.Y('Confidence:Q', title='Confidence Score', scale=alt.Scale(domain=[0, 1])),
#                     color='Model:N',
#                     tooltip=['Model', 'Confidence', 'Latency']
#                 ).properties(width=800, height=400)
#                 st.altair_chart(bar_chart)
#                                 # Latency vs Confidence Scatter Plot
#                 st.subheader("📌Latency vs Confidence")
#                 scatter = alt.Chart(responses).mark_circle(size=60).encode(
#                     x=alt.X('Latency:Q', title='Latency (seconds)'),  # Use numerical value
#                     y='Confidence:Q',
#                     color='Model:N',
#                     # Show formatted string in tooltip
#                     tooltip=['Model', 'Confidence', 'Latency_str:N']
#                 ).properties(width=600, height=300)
#                 st.altair_chart(scatter)
               
#             else:
#                 st.warning("No response data available for visualization")
            
#             with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
#                 json.dump(result, f, indent=2)
#                 tmp_file = f.name
            
#             with open(tmp_file, "rb") as f:
#                 st.download_button("⬇️ Download Results", f, "consortium_results.json", "application/json")

# if __name__ == "__main__":
#         main()
import streamlit as st
from llm_consortium.core.runner_sql import ConsortiumRunnerSQL
from llm_consortium.config.models import ConsortiumConfig
import asyncio
import json
import tempfile
import pandas as pd
import altair as alt
from llm_consortium.utils.pricing import MODEL_PRICING, AVG_INPUT_TOKENS, AVG_OUTPUT_TOKENS, calculate_cost

def main():
    st.set_page_config(layout="wide", page_title="LLM Consortium")
    
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; }
        div[data-testid="stHorizontalBlock"] { gap: 0.5rem; }
        </style>
        """, unsafe_allow_html=True
    )
    
    st.title("🔍 LLM Consortium - Multi-Model Evaluation")
    
    runner_sql=ConsortiumRunnerSQL()
    if 'models' not in st.session_state:
        st.session_state.models = []
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("⚙️ Configuration")
        model_selector = st.selectbox("Select Model", ["gpt-4o-mini", "gpt-3.5-turbo", "gemini-2", "o3-mini"])
        instance_count = st.number_input("Instances", min_value=1, value=1, step=1)
        
        if st.button("➕ Add Model"):
            st.session_state.models = {(m, c) if m != model_selector else (m, instance_count) for m, c in st.session_state.models}
            st.session_state.models.add((model_selector, instance_count))
            st.rerun()
        
        if st.session_state.models:
            st.write("### Selected Models")
            for idx, (model, count) in enumerate(st.session_state.models):
                cols = st.columns([4, 2, 1])
                with cols[0]:
                    st.markdown(f"**{model}**")
                with cols[1]:
                    st.markdown(f"Instances: {count}")
                with cols[2]:
                    if st.button("❌", key=f"delete_{idx}"):
                        st.session_state.models.remove((model, count))
                        st.rerun()
        else:
            st.info("No models added yet")
        
        arbiter = st.selectbox("Arbiter Model", ["gpt-4o-mini", "gemini-2", "gpt-3.5-turbo"], index=2)
        confidence = st.slider("Confidence Threshold", 0.0, 1.0, 0.8)
        max_iter = st.number_input("Max Iterations", min_value=1, value=3, step=1)
        min_iter = st.number_input("Min Iterations", min_value=1, value=1, step=1)
    
    with col2:
        st.subheader("🚀 Execution")
        """this prompt is for prompt eval"""
       
        # Add CSV upload 
        uploaded_file = st.file_uploader(
            "Upload CSV with queries", 
            type=["csv"],
            help="CSV must contain 'db_id' and 'question' columns"
        )
        
        # Display cost estimation only when CSV is uploaded
        if uploaded_file is not None:
            if st.session_state.models:
                models_dict = {model: count for model, count in st.session_state.models}
                total_cost, cost_df = calculate_cost(
                    [(m, c) for m, c in models_dict.items()] + [(arbiter, 1)], 
                    max_iter
                )
                st.write(f"**💰 Estimated Cost:** ${total_cost:.4f}")
                st.dataframe(cost_df, use_container_width=True)
            else:
                st.info("Add models to see cost estimation")
        #prompt = st.text_area("Enter NLQ Prompt", height=150) 
        # if st.session_state.models:
        #     models_dict = {model: count for model, count in st.session_state.models}
        #     total_cost, cost_df = calculate_cost([(m, c) for m, c in models_dict.items()] + [(arbiter, 1)], max_iter)
        #     st.write(f"**💰 Estimated Cost:** ${total_cost:.4f}")
        #     st.dataframe(cost_df, use_container_width=True)
        # else:
        #     st.info("Add models to see cost estimation")
        
        if st.button("▶️ Run Consortium", type="primary"):
            if not st.session_state.models:
                st.error("Please add at least one model")
                return
            if not uploaded_file:
                st.error("Please upload a CSV file first")
                return

            # Save uploaded file to temp
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                csv_path = tmp_file.name
            
            config = ConsortiumConfig(
                models=models_dict,
                arbiter=arbiter,
                confidence_threshold=confidence,
                max_iterations=int(max_iter),
                min_iterations=int(min_iter)
            )
            #un_consortium(config,path) for propmt eval
            result = asyncio.run(runner_sql.run_consortium(config,csv_path))
            
            st.subheader("📊 Results")
            st.write(f"**🔢 Actual Iterations:** {result.get('iterations', max_iter)}")
            st.write(f"**📈 Final Cost:** ${total_cost:.4f}")
            st.write(f"**📝 Synthesized Response:** {result.get('synthesis', {}).get('text', 'No synthesis result')}")
            
            # responses = pd.DataFrame([
            #     {
            #         "Model": r.get("model", "Unknown"),
            #         "Confidence": r.get("confidence", 0),
            #         "Latency": f"{r.get('latency', 0):.2f}s",
            #         "Response": r.get("response", "")[:100] + "..."
            #     } for r in result.get("raw_responses", [])
            # ])
            responses = pd.DataFrame([
                {
                    "Model": r.get("model", "Unknown"),
                    "Confidence": r.get("confidence", 0),
                    "Response": r.get("response", "")[:100] + "...",
                    # Store latency as float, add formatted version for display
                    "Latency": r.get("latency", 0),  # Keep as numerical value
                    "Latency_str": f"{r.get('latency', 0):.2f}s"  # For display
                } for r in result.get("raw_responses", [])
                ])
            st.dataframe(responses, use_container_width=True)
            
            if not responses.empty:
                st.subheader("📌 Model Confidence Comparison")
                bar_chart = alt.Chart(responses).mark_bar().encode(
                    x=alt.X('Model:N', title='Model'),
                    y=alt.Y('Confidence:Q', title='Confidence Score', scale=alt.Scale(domain=[0, 1])),
                    color='Model:N',
                    tooltip=['Model', 'Confidence', 'Latency']
                ).properties(width=800, height=400)
                st.altair_chart(bar_chart)
                                # Latency vs Confidence Scatter Plot
                st.subheader("📌Latency vs Confidence")
                scatter = alt.Chart(responses).mark_circle(size=60).encode(
                    x=alt.X('Latency:Q', title='Latency (seconds)'),  # Use numerical value
                    y='Confidence:Q',
                    color='Model:N',
                    # Show formatted string in tooltip
                    tooltip=['Model', 'Confidence', 'Latency_str:N']
                ).properties(width=600, height=300)
                st.altair_chart(scatter)
               
            else:
                st.warning("No response data available for visualization")
            
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                json.dump(result, f, indent=2)
                tmp_file = f.name
            
            with open(tmp_file, "rb") as f:
                st.download_button("⬇️ Download Results", f, "consortium_results.json", "application/json")

if __name__ == "__main__":
    main()
