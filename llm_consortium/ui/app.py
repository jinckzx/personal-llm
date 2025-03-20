import gradio as gr
from llm_consortium.core.consortium import ConsortiumRunner
from llm_consortium.config.models import ConsortiumConfig
import asyncio
import json
import tempfile
import os
from pathlib import Path

import json
def create_ui():
    runner = ConsortiumRunner()
    
    with gr.Blocks(title="LLM Consortium Manager") as ui:
        gr.Markdown("# LLM Consortium Orchestrator")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("## Configuration")
                
                with gr.Group():
                    model_selector = gr.Dropdown(
                        ["gpt-4o-mini", "gpt-3.5-turbo", "gemini-2", "o3-mini"],
                        label="Select Model"
                    )
                    instance_count = gr.Number(1, label="Instances", precision=0)
                    add_model_btn = gr.Button("Add Model")
                
                model_list = gr.Dataframe(
                    headers=["Model", "Instances"],
                    datatype=["str", "number"],
                    interactive=False
                )
                
                arbiter = gr.Dropdown(
                    ["gpt-4o-mini", "gemini-2","gpt-3.5-turbo"],
                    label="Arbiter Model",
                    value="gpt-3.5-turbo"
                )
                
                confidence = gr.Slider(0, 1, 0.8, label="Confidence Threshold")
                max_iter = gr.Number(3, label="Max Iterations", precision=0)
                min_iter = gr.Number(1, label="Min Iterations", precision=0)
            
            with gr.Column(scale=2):
                gr.Markdown("## Execution")
                prompt = gr.Textbox(label="Input Prompt", lines=5)
                run_btn = gr.Button("Run Consortium", variant="primary")
                
                gr.Markdown("## Results")
                synthesis = gr.Textbox(label="Synthesized Answer", interactive=False)
                dissenting_views = gr.Textbox(label="Dissenting View", interactive=False)
                analysis = gr.Textbox(label="Analysis", interactive=False)
                confidence_out = gr.Number(label="Confidence Score")
                
                gr.Markdown("### Individual Responses")
                responses = gr.DataFrame(
                    headers=["Model", "Response", "Confidence", "Latency"],
                    row_count=10
                )
                
                download = gr.DownloadButton("Download Results")
        
        # Model management
        models = []
        
        def add_model(model, count):
            models.append((model, int(count)))
            return models
        
        add_model_btn.click(
            add_model,
            [model_selector, instance_count],
            [model_list]
        )
   
        # def run_consortium(prompt, model_list, arbiter, confidence, max_iter, min_iter):
            # # Convert model_list DataFrame to a dictionary
            # models_dict = {}
            # for _, row in model_list.iterrows():
            #     model_name = row["Model"]
            #     instance_count = row["Instances"]
            #     models_dict[model_name] = instance_count
            
        #     # Create ConsortiumConfig
        #     config = ConsortiumConfig(
        #         models=models_dict,
        #         arbiter=arbiter,
        #         confidence_threshold=confidence,
        #         max_iterations=int(max_iter),
        #         min_iterations=int(min_iter)
        #     )
            
        #     # Run the consortium
        #     result = asyncio.run(runner.run_consortium(config, prompt))
            
      
            
        #     # Format the results
        #     return {
        #         synthesis: result["synthesis"]["text"],
        #         analysis: result["synthesis"]["analysis"],
        #         confidence_out: result["synthesis"]["confidence"],
        #         responses: [[
        #             r["model"],  # Access dictionary keys instead of attributes
        #             r["response"][:100] + "..." if len(r["response"]) > 100 else r["response"],
        #             r["confidence"],
        #             f"{r['latency']:.2f}s"
        #         ] for r in result["raw_responses"]],  # raw_responses is a list of dictionaries
        #         download: temp_file_path  # Return the file path instead of JSON string
        #     }
        def run_consortium(prompt, model_list, arbiter, confidence, max_iter, min_iter):
            # Convert model_list from list of lists to dictionary
            # models_dict = {row[0]: int(row[1]) for row in model_list}  
            #             # Convert model_list DataFrame to a dictionary
            models_dict = {}
            for _, row in model_list.iterrows():
                model_name = row["Model"]
                instance_count = row["Instances"]
                models_dict[model_name] = instance_count
            # Create ConsortiumConfig
            config = ConsortiumConfig(
                models=models_dict,
                arbiter=arbiter,
                confidence_threshold=confidence,
                max_iterations=int(max_iter),
                min_iterations=int(min_iter)
            )

            # Run the consortium
            result = asyncio.run(runner.run_consortium(config, prompt))

          
                  # Save the result to a temporary JSON file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_file:
                json.dump(result, temp_file, indent=2)
                temp_file_path = temp_file.name

            # Ensure all expected keys exist in result
            return {
                synthesis: result.get("synthesis", {}).get("text", "No synthesis result"),
                analysis: result.get("synthesis", {}).get("analysis", "No analysis available"),
                dissenting_views: result.get("synthesis", {}).get("dissenting_views", "No dissenting views"),
                confidence_out: result.get("synthesis", {}).get("confidence", 0),
                responses: [[
                    r.get("model", "Unknown"),
                    r.get("response", "")[:100] + "..." if len(r.get("response", "")) > 100 else r.get("response", ""),
                    r.get("confidence", 0),
                    f"{r.get('latency', 0):.2f}s"
                ] for r in result.get("raw_responses", [])],  
                download: temp_file_path  
            }

        """changes made since it was expecting dictionary but my df was sending"""
        run_btn.click(
            run_consortium,
            [prompt, model_list, arbiter, confidence, max_iter, min_iter],
            [synthesis, analysis, dissenting_views, confidence_out, responses, download]
        )
    
    return ui
