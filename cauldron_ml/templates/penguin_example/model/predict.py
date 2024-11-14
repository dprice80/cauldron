from models import (
    get_latest_model_from_gcp,
    create_predictions
)
from utils.vertex import initialise_pipeline

if __name__ == "__main__":

    pipeline_settings = initialise_pipeline()
    
    # You will need to update the model_id in the config/inputs.json file. 
    # You can find this in the model registry

    print("Loading model from bucket...")
    model = get_latest_model_from_gcp(pipeline_settings)
    
    print("Creating predictions...")
    predictions = create_predictions(model)

    print(predictions)

