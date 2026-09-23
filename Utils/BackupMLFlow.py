# MLFLOW API SUCKS!!!!!!!!!!!

# despite what the MLFlow API documentation says, the prompts_page does not include a prompt.template value

# import json
# import mlflow

# # 1. Fetch prompts from your registry 
# # If using Databricks Unity Catalog, define your filter string like: "catalog = 'main' AND schema = 'default'"
# prompts_page = mlflow.genai.search_prompts()

# backup_data = []

# # 2. Iterate through the PagedList to extract prompt details
# for prompt in prompts_page:
#     backup_data.append({
#         "name": prompt.name,
#         "version": getattr(prompt, "version", None),  # Extract version if tracking distinct iterations
#         "tags": prompt.tags,
#         # .template contains the unexecuted text string or chat role structures
#         "template": prompt.template 
#     })

# # 3. Write out the templates to a local backup file
# backup_filename = "mlflow_prompts_backup.json"
# with open(backup_filename, "w", encoding="utf-8") as f:
#     json.dump(backup_data, f, indent=4, ensure_ascii=False)

# print(f"Successfully backed up {len(backup_data)} prompt templates to {backup_filename}!")


# from mlflow.tracking import MlflowClient
# import json




# client = MlflowClient()
# all_prompts = []
# token = None

# # Paginate through all matching records
# while True:
#     page = client.search_prompts(
#         max_results=50,
#         page_token=token,
#     )
    
#     for prompt in page:
#         all_prompts.append({
#             "name": prompt.name,
#             "template": prompt.template, # this line always errors
#             "tags": prompt.tags
#         })
        
#     token = page.token
#     if not token:
#         break

# # Export all pages to your backup file
# with open("comprehensive_prompts_backup.json", "w") as f:
#     json.dump(all_prompts, f, indent=4)
    
    
    
import mlflow
import json

# Fetch your specific runs or prompt templates from the MLflow registry/tracking
client = mlflow.tracking.MlflowClient()
# Example: loop through runs to extract logged prompt parameters
runs = client.search_runs(experiment_ids=["0"])


prompts_backup = {}
for run in runs:
    # Adapt 'prompt' to whatever key name you used to log your prompts
    if 'prompt' in run.data.params:
        prompts_backup[run.info.run_id] = {
            "run_name": run.info.run_name,
            "prompt": run.data.params['prompt']
        }

# Save as a clean text file that Git CAN track easily
with open("mlflow_prompts_backup.json", "w") as f:
    json.dump(prompts_backup, f, indent=4)

